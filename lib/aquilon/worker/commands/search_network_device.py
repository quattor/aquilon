# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
"""Contains the logic for `aq search network_device`."""

from sqlalchemy.orm import subqueryload, joinedload, contains_eager, undefer

from aquilon.aqdb.model import NetworkDevice, DnsRecord, Fqdn, DnsDomain
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.hardware_entity import search_hardware_entity_query
from aquilon.worker.formats.list import StringAttributeList


class CommandSearchNetworkDevice(BrokerCommand):

    required_parameters = []

    def render(self, session, network_device, type, vlan, fullinfo, style,
               **arguments):
        q = search_hardware_entity_query(session, hardware_type=NetworkDevice,
                                         **arguments)
        if type:
            q = q.filter_by(switch_type=type)
        if network_device:
            dbnetdev = NetworkDevice.get_unique(session, network_device, compel=True)
            q = q.filter_by(id=dbnetdev.id)

        if vlan:
            q = q.join("observed_vlans", "port_group").filter_by(network_tag=vlan)
            q = q.reset_joinpoint()

        # Prefer the primary name for ordering
        q = q.outerjoin(DnsRecord, (Fqdn, DnsRecord.fqdn_id == Fqdn.id),
                        DnsDomain)
        q = q.options(contains_eager('primary_name'),
                      contains_eager('primary_name.fqdn'),
                      contains_eager('primary_name.fqdn.dns_domain'))
        q = q.reset_joinpoint()
        q = q.order_by(Fqdn.name, DnsDomain.name, NetworkDevice.label)

        if fullinfo or style != 'raw':
            q = q.options(joinedload('location'),
                          subqueryload('interfaces'),
                          joinedload('interfaces.assignments'),
                          joinedload('interfaces.assignments.dns_records'),
                          joinedload('interfaces.assignments.network'),
                          subqueryload('observed_macs'),
                          undefer('observed_macs.creation_date'),
                          subqueryload('observed_vlans'),
                          joinedload('observed_vlans.port_group'),
                          undefer('observed_vlans.port_group.creation_date'),
                          joinedload('observed_vlans.port_group.network'),
                          subqueryload('model'),
                          # Switches don't have machine specs, but the formatter
                          # checks for their existence anyway
                          joinedload('model.machine_specs'))
            return q.all()
        return StringAttributeList(q.all(), "printable_name")
