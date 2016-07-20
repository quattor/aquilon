# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013,2014,2015,2016  Contributor
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
"""Contains the logic for `aq add interface address`."""

from aquilon.utils import validate_nlist_key
from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.aqdb.model import (HardwareEntity, NetworkEnvironment, Interface,
                                ManagementInterface, ARecord)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.dns import grab_address
from aquilon.worker.dbwrappers.interface import (generate_ip,
                                                 assign_address)
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.dbwrappers.location import get_default_dns_domain
from aquilon.worker.templates import Plenary, PlenaryCollection


class CommandAddInterfaceAddress(BrokerCommand):

    required_parameters = ['interface']

    def render(self, session, logger, machine, chassis, network_device, fqdn,
               shortname, interface, label, network_environment, map_to_primary,
               shared, priority, **kwargs):

        if machine:
            hwtype = 'machine'
            hwname = machine
        elif chassis:
            hwtype = 'chassis'
            hwname = chassis
        elif network_device:
            hwtype = 'network_device'
            hwname = network_device

        if shared and not network_device:
            raise ArgumentError("The --shared option can only be used with "
                                "network devices.")

        dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                             network_environment)

        dbhw_ent = HardwareEntity.get_unique(session, hwname,
                                             hardware_type=hwtype, compel=True)
        dbinterface = Interface.get_unique(session, hardware_entity=dbhw_ent,
                                           name=interface, compel=True)

        oldinfo = DSDBRunner.snapshot_hw(dbhw_ent)

        audit_results = []
        ip = generate_ip(session, logger, dbinterface,
                         network_environment=dbnet_env,
                         audit_results=audit_results, **kwargs)

        if dbinterface.interface_type == "loopback":
            # Switch loopback interfaces may use e.g. the network address as an
            # IP address
            relaxed = True
        else:
            relaxed = False

        if not fqdn:
            # For shared addresses, we want to re-use the DNS record if it
            # already exists. We don't want to "steal" non-shared records,
            # though.
            if shared and ip and not shortname:
                dbnetwork = get_net_id_from_ip(session, ip, network_environment)
                q = session.query(ARecord)
                q = q.filter_by(ip=ip, network=dbnetwork)
                dbdns_rec = q.first()
                if dbdns_rec:
                    fqdn = str(dbdns_rec)

            if dbhw_ent.primary_name:
                dbdns_domain = dbhw_ent.primary_name.fqdn.dns_domain
            else:
                dbdns_domain = get_default_dns_domain(dbhw_ent.location)

            if not shortname:
                if not dbhw_ent.primary_name:
                    raise ArgumentError("{0} has no primary name, can not "
                                        "auto-generate the DNS record.  "
                                        "Please specify --fqdn.".format(dbhw_ent))

                if isinstance(dbinterface, ManagementInterface):
                    shortname = "%sr" % dbhw_ent.primary_name.fqdn.name
                elif label:
                    shortname = "%s-%s-%s" % (dbhw_ent.primary_name.fqdn.name,
                                              dbinterface.name, label)
                else:
                    shortname = "%s-%s" % (dbhw_ent.primary_name.fqdn.name,
                                           dbinterface.name)

            fqdn = "%s.%s" % (shortname, dbdns_domain)
            logger.info("Selected FQDN {0!s} for {1:l}."
                        .format(fqdn, dbinterface))
            audit_results.append(('fqdn', fqdn))

        if label is None:
            label = ""

        # The label will be used as an nlist key
        if label:
            validate_nlist_key("label", label)

        # TODO: add allow_multi=True
        dbdns_rec, newly_created = grab_address(session, fqdn, ip, dbnet_env,
                                                relaxed=relaxed, allow_shared=shared)
        ip = dbdns_rec.ip
        dbnetwork = dbdns_rec.network
        delete_old_dsdb_entry = not newly_created and not dbdns_rec.assignments

        # Reverse PTR control. Auxiliary addresses should point to the primary
        # name by default, with some exceptions.
        if (map_to_primary is None and dbhw_ent.primary_name and
                dbinterface.interface_type != "management" and
                dbdns_rec.fqdn.dns_environment == dbhw_ent.primary_name.fqdn.dns_environment):
            map_to_primary = True

        if map_to_primary:
            if not dbhw_ent.primary_name:
                raise ArgumentError("{0} does not have a primary name, cannot "
                                    "set the reverse DNS mapping."
                                    .format(dbhw_ent))
            if (dbhw_ent.primary_name.fqdn.dns_environment !=
                    dbdns_rec.fqdn.dns_environment):
                raise ArgumentError("{0} lives in {1:l}, not {2:l}."
                                    .format(dbhw_ent,
                                            dbhw_ent.primary_name.fqdn.dns_environment,
                                            dbdns_rec.fqdn.dns_environment))
            if dbinterface.interface_type == "management":
                raise ArgumentError("The reverse PTR for management addresses "
                                    "should not point to the primary name.")
            dbdns_rec.reverse_ptr = dbhw_ent.primary_name.fqdn

        # Check that the network ranges assigned to different interfaces
        # do not overlap even if the network environments are different, because
        # that would confuse routing on the host. E.g. if eth0 is an internal
        # and eth1 is an external interface, then using 192.168.1.10/24 on eth0
        # and using 192.168.1.20/26 on eth1 won't work.
        for addr in dbhw_ent.all_addresses():
            if addr.network != dbnetwork and \
               addr.network.network.overlaps(dbnetwork.network):
                raise ArgumentError("{0} in {1:l} used on {2:l} overlaps "
                                    "requested {3:l} in "
                                    "{4:l}.".format(addr.network,
                                                    addr.network.network_environment,
                                                    addr.interface,
                                                    dbnetwork,
                                                    dbnetwork.network_environment))

        assign_address(dbinterface, ip, dbnetwork, label=label, shared=shared,
                       priority=priority, logger=logger)
        session.flush()

        plenaries = PlenaryCollection(logger=logger)
        plenaries.append(Plenary.get_plenary(dbhw_ent))
        plenaries.append(Plenary.get_plenary(dbnetwork))
        if dbhw_ent.host:
            plenaries.append(Plenary.get_plenary(dbhw_ent.host))

        dsdb_runner = DSDBRunner(logger=logger)

        if shared and newly_created:
            # Mimic the logic from DSDBRunner.snapshot_hw()
            if dbinterface.comments:
                comments = dbinterface.comments
            elif dbinterface.interface_type != 'management':
                comments = dbhw_ent.comments
            else:
                comments = None
            dsdb_runner.add_host_details(dbdns_rec, ip, comments=comments)

        with plenaries.transaction():
            if dbhw_ent.host and dbhw_ent.host.archetype.name == 'aurora':
                try:
                    dsdb_runner.show_host(dbdns_rec.fqdn.name)
                except ProcessException as e:
                    raise ArgumentError("Could not find host in DSDB: "
                                        "%s" % e)
            else:
                if delete_old_dsdb_entry:
                    dsdb_runner.delete_host_details(dbdns_rec.fqdn, ip)
                dsdb_runner.update_host(dbhw_ent, oldinfo)
                dsdb_runner.commit_or_rollback("Could not add host to DSDB")

        for name, value in audit_results:
            self.audit_result(session, name, value, **kwargs)
        return
