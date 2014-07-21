# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013,2014  Contributor
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
from sqlalchemy.orm import undefer

from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import (Network, Machine, VlanInfo, ObservedVlan,
                                Cluster, ARecord, DynamicStub,
                                NetworkEnvironment)
from aquilon.aqdb.model.dns_domain import parse_fqdn
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.formats.list import StringAttributeList
from aquilon.aqdb.model.network import get_net_id_from_ip


class CommandSearchNetwork(BrokerCommand):

    required_parameters = []

    def render(self, session, network, network_environment, ip, type, side,
               machine, fqdn, cluster, pg, has_dynamic_ranges, exact_location,
               fullinfo, style, **arguments):
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
        if machine:
            dbmachine = Machine.get_unique(session, machine, compel=True)
            vlans = []
            if dbmachine.cluster and dbmachine.cluster.network_device:
                # If this is a VM on a cluster, consult the VLANs.  There
                # could be functionality here for real hardware to consult
                # interface port groups... there's no real use case yet.
                vlans = [VlanInfo.get_by_pg(session, i.port_group).vlan_id
                         for i in dbmachine.interfaces if i.port_group]
                if vlans:
                    q = q.join('observed_vlans')
                    q = q.filter_by(network_device=dbmachine.cluster.network_device)
                    q = q.filter(ObservedVlan.vlan_id.in_(vlans))
                    q = q.reset_joinpoint()
            if not vlans:
                networks = [addr.network.id for addr in
                            dbmachine.all_addresses()]
                if not networks:
                    msg = "Machine %s has no interfaces " % dbmachine.label
                    if dbmachine.cluster:
                        msg += "with a portgroup or "
                    msg += "assigned to a network."
                    raise ArgumentError(msg)
                q = q.filter(Network.id.in_(networks))
        if fqdn:
            (short, dbdns_domain) = parse_fqdn(session, fqdn)
            dnsq = session.query(ARecord.ip)
            dnsq = dnsq.join(ARecord.fqdn)
            dnsq = dnsq.filter_by(name=short)
            dnsq = dnsq.filter_by(dns_domain=dbdns_domain)
            networks = [get_net_id_from_ip(session, addr.ip, dbnet_env).id
                        for addr in dnsq.all()]
            q = q.filter(Network.id.in_(networks))
        if cluster:
            dbcluster = Cluster.get_unique(session, cluster, compel=True)
            if dbcluster.network_device:
                q = q.join('observed_vlans')
                q = q.filter_by(network_device=dbcluster.network_device)
                q = q.reset_joinpoint()
            else:
                net_ids = [h.hardware_entity.primary_name.network.id for h in
                           dbcluster.hosts if getattr(h.hardware_entity.primary_name,
                                                      "network")]
                q = q.filter(Network.id.in_(net_ids))
        if pg:
            dbvi = VlanInfo.get_by_pg(session, pg, compel=ArgumentError)
            q = q.join('observed_vlans')
            q = q.filter_by(vlan_id=dbvi.vlan_id)
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
        if fullinfo or style != 'raw':
            q = q.options(undefer('comments'))
            return q.all()
        return StringAttributeList(q.all(),
                                   lambda n: "%s/%s" % (n.ip, n.cidr))
