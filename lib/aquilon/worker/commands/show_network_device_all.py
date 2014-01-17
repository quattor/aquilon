# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013,2014  Contributor
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
"""Contains the logic for `aq show network_device --all`."""

from sqlalchemy.orm import (subqueryload, joinedload, lazyload, contains_eager,
                            undefer)

from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import NetworkDevice, DnsRecord, DnsDomain, Fqdn


class CommandShowNetworkDeviceAll(BrokerCommand):

    def render(self, session, **arguments):
        q = session.query(NetworkDevice)

        q = q.options(subqueryload('location'),
                      subqueryload('interfaces'),
                      lazyload('interfaces.hardware_entity'),
                      joinedload('interfaces.assignments'),
                      joinedload('interfaces.assignments.dns_records'),
                      joinedload('interfaces.assignments.network'),
                      subqueryload('observed_macs'),
                      undefer('observed_macs.creation_date'),
                      subqueryload('observed_vlans'),
                      undefer('observed_vlans.creation_date'),
                      joinedload('observed_vlans.network'),
                      subqueryload('model'),
                      # Switches don't have machine specs, but the formatter
                      # checks for their existence anyway
                      joinedload('model.machine_specs'))

        # Prefer the primary name for ordering
        q = q.outerjoin(DnsRecord, (Fqdn, DnsRecord.fqdn_id == Fqdn.id),
                        DnsDomain)
        q = q.options(contains_eager('primary_name'),
                      contains_eager('primary_name.fqdn'),
                      contains_eager('primary_name.fqdn.dns_domain'))
        q = q.reset_joinpoint()
        q = q.order_by(Fqdn.name, DnsDomain.name, NetworkDevice.label)

        return q.all()
