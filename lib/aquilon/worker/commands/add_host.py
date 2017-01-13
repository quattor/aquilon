# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Contains the logic for `aq add host`."""

from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.aqdb.model import (Machine, ServiceAddress, HostResource,
                                Archetype)
from aquilon.utils import validate_nlist_key
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.dns import grab_address
from aquilon.worker.dbwrappers.interface import (generate_ip, assign_address,
                                                 get_interfaces)
from aquilon.worker.dbwrappers.host import create_host
from aquilon.worker.processes import DSDBRunner


def get_boot_interface(dbmachine):
    dbinterface = None
    # Look up the boot interface
    for iface in dbmachine.interfaces:
        if iface.bootable:
            dbinterface = iface
            # If the boot interface is enslaved in a bonding/bridge setup,
            # then assign the address to the master instead
            while dbinterface.master:
                dbinterface = dbinterface.master
            break
    return dbinterface


class CommandAddHost(BrokerCommand):
    requires_plenaries = True

    required_parameters = ["hostname", "machine", "archetype"]

    def render(self, session, logger, plenaries, hostname, machine, archetype,
               zebra_interfaces, skip_dsdb_check=False, **arguments):
        dbarchetype = Archetype.get_unique(session, archetype, compel=True)
        dbmachine = Machine.get_unique(session, machine, compel=True)

        if (dbmachine.model.model_type.isAuroraNode() and
                dbarchetype.name != 'aurora'):
            raise ArgumentError("Machines of type aurora_node can only be "
                                "added with archetype aurora.")

        if dbmachine.host:
            raise ArgumentError("{0:c} {0.label} is already allocated to "
                                "{1:l}.".format(dbmachine, dbmachine.host))

        # IP addresses defined before the host is added have been entered to
        # DSDB with the type 'aquilon', and that's not going to work well for
        # Aurora hosts.
        if dbarchetype.name == 'aurora':
            if list(dbmachine.all_addresses()):
                raise ArgumentError("Having IP addresses assigned before "
                                    "the host object is created is not "
                                    "supported for Aurora hosts.")

        validate_nlist_key('hostname', hostname)

        dsdb_runner = DSDBRunner(logger=logger)
        if dbarchetype.name == 'aurora':
            # For aurora, check that DSDB has a record of the host.
            if not skip_dsdb_check:
                try:
                    dsdb_runner.show_host(hostname)
                except ProcessException as e:
                    raise ArgumentError("Could not find host in DSDB: "
                                        "%s" % e)
            # As the host already exists in DSDB we don't need a snapshot
            oldinfo = None
        else:
            # Create a snapshop of the machine before we create the host; but
            # not for aurora nodes as we dont update DSDB
            oldinfo = DSDBRunner.snapshot_hw(dbmachine)

        create_host(session, logger, self.config, dbmachine, dbarchetype,
                    **arguments)

        if zebra_interfaces:
            # --autoip does not make sense for Zebra (at least not the way it's
            # implemented currently)
            dbinterface = None
        else:
            dbinterface = get_boot_interface(dbmachine)

        # This method is allowed to return None. This can only happen
        # (currently) using add_aurora_host, add_windows_host, or possibly by
        # bypassing the aq client and posting a request directly.
        audit_results = []
        ip = generate_ip(session, logger, dbinterface,
                         audit_results=audit_results, **arguments)

        dbdns_rec, _ = grab_address(session, hostname, ip,
                                    allow_restricted_domain=True,
                                    allow_reserved=True, preclude=True)
        dbmachine.primary_name = dbdns_rec

        # Fix up auxiliary addresses to point to the primary name by default
        if ip:
            dns_env = dbdns_rec.fqdn.dns_environment

            for addr in dbmachine.all_addresses():
                if addr.interface.interface_type == "management":
                    continue
                for rec in addr.dns_records:
                    if rec.fqdn.dns_environment == dns_env:
                        rec.reverse_ptr = dbdns_rec.fqdn

        if zebra_interfaces:
            if not ip:
                raise ArgumentError("Zebra configuration requires an IP address.")
            dbsrv_addr = self.assign_zebra_address(session, dbmachine, dbdns_rec,
                                                   zebra_interfaces)
        else:
            if ip:
                if not dbinterface:
                    raise ArgumentError("You have specified an IP address for the "
                                        "host, but {0:l} does not have a bootable "
                                        "interface.".format(dbmachine))
                assign_address(dbinterface, ip, dbdns_rec.network, logger=logger)
            dbsrv_addr = None

        session.flush()

        plenaries.add(dbmachine)
        if dbmachine.vm_container:
            plenaries.add(dbmachine.vm_container)
        if dbsrv_addr:
            plenaries.add(dbsrv_addr)

        with plenaries.transaction():
            if oldinfo:
                dsdb_runner.update_host(dbmachine, oldinfo)
                dsdb_runner.commit_or_rollback("Could not add host to DSDB")

        for name, value in audit_results:
            self.audit_result(session, name, value, **arguments)
        return

    def assign_zebra_address(self, session, dbmachine, dbdns_rec,
                             zebra_interfaces):
        """ Assign a Zebra-managed address to multiple interfaces """

        # Reset the routing configuration
        for iface in dbmachine.interfaces:
            if iface.default_route:
                iface.default_route = False

        dbifaces = get_interfaces(dbmachine, zebra_interfaces,
                                  dbdns_rec.network)

        for dbinterface in dbifaces:
            # Make sure the transit IPs resolve to the primary name
            for addr in dbinterface.assignments:
                if addr.label:
                    continue
                for dnr in addr.dns_records:
                    dnr.reverse_ptr = dbdns_rec.fqdn

            # Transits should be providers of the default route
            dbinterface.default_route = True

        # Disable autoflush, since the ServiceAddress object won't be complete
        # until it's attached to its holder
        with session.no_autoflush:
            resholder = HostResource(host=dbmachine.host)
            session.add(resholder)
            dbsrv_addr = ServiceAddress(name="hostname", dns_record=dbdns_rec)
            resholder.resources.append(dbsrv_addr)
            dbsrv_addr.interfaces = dbifaces

        return dbsrv_addr
