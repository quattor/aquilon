# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014  Contributor
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


from aquilon.exceptions_ import ArgumentError, UnimplementedError
from aquilon.aqdb.model import ServiceAddress, Cluster, Host
from aquilon.utils import validate_nlist_key
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.interface import assign_address
from aquilon.worker.dbwrappers.dns import grab_address
from aquilon.worker.dbwrappers.resources import (add_resource,
                                                 get_resource_holder)
from aquilon.worker.processes import DSDBRunner


def add_srv_dsdb_callback(session, logger, dbsrv, toplevel_holder=None,
                          oldinfo=None, newly_created=None, comments=None):
    dsdb_runner = DSDBRunner(logger=logger)

    if not newly_created:
        dsdb_runner.delete_host_details(dbsrv.dns_record.fqdn, dbsrv.dns_record.ip)
    if isinstance(toplevel_holder, Host):
        dsdb_runner.update_host(toplevel_holder.hardware_entity, oldinfo)
    else:
        dsdb_runner.add_host_details(dbsrv.dns_record.fqdn,
                                     dbsrv.dns_record.ip, comments=comments)

    dsdb_runner.commit_or_rollback("Could not add host to DSDB")


class CommandAddServiceAddress(BrokerCommand):

    required_parameters = ["service_address", "name", "interfaces"]

    def render(self, session, logger, service_address, ip, name, interfaces,
               hostname, cluster, resourcegroup,
               network_environment, map_to_primary, comments, **arguments):

        validate_nlist_key("name", name)

        # TODO: generalize the error message - Layer-3 failover may be
        # implemented by other software, not just Zebra.
        if name == "hostname":
            raise ArgumentError("The hostname service address is reserved for "
                                "Zebra.  Please specify the --zebra_interfaces "
                                "option when calling add_host if you want the "
                                "primary name of the host to be managed by "
                                "Zebra.")

        ifnames = [ifname.strip().lower() for ifname in interfaces.split(",")]
        if not ifnames:
            raise ArgumentError("Please specify at least one interface name.")

        holder = get_resource_holder(session, hostname, cluster,
                                     resourcegroup, compel=False)
        toplevel_holder = holder.toplevel_holder_object

        ServiceAddress.get_unique(session, name=name, holder=holder,
                                  preclude=True)

        # TODO: add allow_multi=True
        dbdns_rec, newly_created = grab_address(session, service_address, ip,
                                                network_environment)
        ip = dbdns_rec.ip

        if map_to_primary:
            if not isinstance(toplevel_holder, Host):
                raise ArgumentError("The --map_to_primary option works only "
                                    "for host-based service addresses.")
            dbdns_rec.reverse_ptr = toplevel_holder.hardware_entity.primary_name.fqdn

        # Disable autoflush, since the ServiceAddress object won't be complete
        # until add_resource() is called
        with session.no_autoflush:
            dbsrv = ServiceAddress(name=name, dns_record=dbdns_rec,
                                   comments=comments)
            holder.resources.append(dbsrv)

            oldinfo = None
            if isinstance(toplevel_holder, Cluster):
                if not toplevel_holder.hosts:
                    # The interface names are only stored in the
                    # AddressAssignment objects, so we can't handle a cluster
                    # with no hosts and thus no interfaces
                    raise ArgumentError("Cannot assign a service address to a "
                                        "cluster that has no members.")
                for host in toplevel_holder.hosts:
                    apply_service_address(host, ifnames, dbsrv, logger)
            elif isinstance(toplevel_holder, Host):
                oldinfo = DSDBRunner.snapshot_hw(toplevel_holder.hardware_entity)
                apply_service_address(toplevel_holder, ifnames, dbsrv, logger)
            else:  # pragma: no cover
                raise UnimplementedError("{0} as a resource holder is not "
                                         "implemented.".format(toplevel_holder))

        add_resource(session, logger, holder, dbsrv,
                     dsdb_callback=add_srv_dsdb_callback,
                     toplevel_holder=toplevel_holder, oldinfo=oldinfo,
                     newly_created=newly_created, comments=comments)

        return


def apply_service_address(dbhost, ifnames, srv_addr, logger):
    for ifname in ifnames:
        dbinterface = None
        for iface in dbhost.hardware_entity.interfaces:
            if iface.name == ifname:
                dbinterface = iface
                break
        if not dbinterface:
            raise ArgumentError("{0} does not have an interface named "
                                "{1}.".format(dbhost.hardware_entity, ifname))

        assign_address(dbinterface, srv_addr.dns_record.ip,
                       srv_addr.dns_record.network, label=srv_addr.name,
                       resource=srv_addr, logger=logger)
