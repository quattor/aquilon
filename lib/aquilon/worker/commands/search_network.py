# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013,2014,2015,2016,2017  Contributor
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
"""Contains the logic for `aq search network`."""

from sqlalchemy.sql import exists
from sqlalchemy.orm import undefer, joinedload, subqueryload, aliased

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import (Network, Machine, VlanInfo, PortGroup, Cluster,
                                VirtualSwitch, ARecord, DynamicStub,
                                NetworkEnvironment, NetworkCompartment)
from aquilon.aqdb.model.dns_domain import parse_fqdn
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.formats.network import NetworkHostList, NetworkList


class CommandSearchNetwork(BrokerCommand):

    required_parameters = []

    def render(self, session, network, network_environment, ip, type, side,
               machine, fqdn, cluster, virtual_switch, pg, has_dynamic_ranges,
               exact_location, fullinfo, style, network_compartment,
               **arguments):
        """Return a network matching the parameters.

        Some of the search terms can only return a unique network.  For
        those (like ip and fqdn) we proceed with the query anyway.  This
        allows for quick scripted tests like "is the network for X.X.X.X
        a tor_net2?".

        """
        dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                             network_environment)
        q = session.query(Network)
        q = q.filter_by(network_environment=dbnet_env)
        if network:
            # Note: the network name is not unique (neither in QIP)
            q = q.filter_by(name=network)
        if ip:
            dbnetwork = get_net_id_from_ip(session, ip, dbnet_env)
            q = q.filter_by(id=dbnetwork.id)
        if type:
            q = q.filter_by(network_type=type)
        if side:
            q = q.filter_by(side=side)
        if network_compartment:
            dbcomp = NetworkCompartment.get_unique(session,
                                                   network_compartment,
                                                   compel=True)
            q = q.filter_by(network_compartment=dbcomp)
        if machine:
            dbmachine = Machine.get_unique(session, machine, compel=True)
            # If this is a VM, consult the port groups.  There
            # could be functionality here for real hardware to consult
            # interface port groups... there's no real use case yet.
            networks = set(iface.port_group.network_id
                           for iface in dbmachine.interfaces
                           if iface.port_group)
            networks.update(addr.network.id for addr in
                            dbmachine.all_addresses())
            if not networks:
                raise ArgumentError("{0} has no interfaces with a port group "
                                    "or assigned to a network."
                                    .format(dbmachine))
            q = q.filter(Network.id.in_(networks))
        if fqdn:
            (short, dbdns_domain) = parse_fqdn(session, fqdn)
            dnsq = session.query(ARecord.ip)
            dnsq = dnsq.join(ARecord.fqdn)
            dnsq = dnsq.filter_by(name=short)
            dnsq = dnsq.filter_by(dns_domain=dbdns_domain)
            networks = [get_net_id_from_ip(session, addr.ip, dbnet_env).id
                        for addr in dnsq]
            q = q.filter(Network.id.in_(networks))
        if cluster:
            dbcluster = Cluster.get_unique(session, cluster, compel=True)
            if dbcluster.network_device:
                # Old ESX model
                net_ids = [dbpg.network_id for dbpg in
                           dbcluster.network_device.port_groups]
            else:
                # Non-ESX
                # TODO: should this include all networks used by the members?
                net_ids = [h.hardware_entity.primary_name.network.id for h in
                           dbcluster.hosts if getattr(h.hardware_entity.primary_name,
                                                      "network")]
            # Filtering on an empty list is an expensive way to return
            # nothing...
            if net_ids:
                q = q.filter(Network.id.in_(net_ids))
            else:
                q = q.filter(False)
        if pg or virtual_switch:
            PGAlias = aliased(PortGroup)
            q = q.join(PGAlias, Network.port_group)
            if pg:
                dbvi = VlanInfo.get_by_pg(session, pg, compel=False)

                if dbvi:
                    q = q.filter_by(network_tag=dbvi.vlan_id, usage=dbvi.vlan_type)
                else:
                    usage, network_tag = PortGroup.parse_name(pg)
                    if network_tag is not None:
                        q = q.filter_by(network_tag=network_tag, usage=usage)
                    else:
                        q = q.filter_by(usage=pg)
            if virtual_switch:
                dbvswitch = VirtualSwitch.get_unique(session, virtual_switch,
                                                     compel=True)
                q = q.filter(PGAlias.virtual_switches.contains(dbvswitch))
            q = q.reset_joinpoint()
        dblocation = get_location(session, **arguments)
        if dblocation:
            if exact_location:
                q = q.filter_by(location=dblocation)
            else:
                childids = dblocation.offspring_ids()
                q = q.filter(Network.location_id.in_(childids))
        if has_dynamic_ranges:
            q = q.filter(exists([DynamicStub.dns_record_id],
                                from_obj=DynamicStub.__table__.join(ARecord.__table__))
                         .where(Network.id == DynamicStub.network_id))
        q = q.order_by(Network.ip)
        if fullinfo:
            q = q.options([undefer('comments'),
                           joinedload('location'),
                           subqueryload("assignments"),
                           joinedload("assignments.interface"),
                           joinedload("assignments.interface.hardware_entity"),
                           joinedload("assignments.dns_records"),
                           subqueryload("routers"),
                           subqueryload("network_compartment"),
                           subqueryload("dynamic_stubs")])
            return NetworkHostList(q.all())
        return NetworkList(q.all())
