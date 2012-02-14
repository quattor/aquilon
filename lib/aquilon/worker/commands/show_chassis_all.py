# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013  Contributor
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
"""Contains the logic for `aq show chassis`."""


from sqlalchemy.orm import subqueryload, joinedload, lazyload, contains_eager

from aquilon.aqdb.model import Chassis, DnsRecord, DnsDomain, Fqdn
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.formats.list import StringAttributeList


class CommandShowChassisAll(BrokerCommand):

    required_parameters = []

    def render(self, session, fullinfo, **arguments):
        q = session.query(Chassis)

        if fullinfo:
            q = q.options(subqueryload('model'),
                          joinedload('model.machine_specs'),
                          subqueryload('location'),
                          joinedload('slots'),
                          subqueryload('slots.machine'),

                          # A rare case when we don't need primary name/host
                          lazyload('slots.machine.primary_name'),
                          lazyload('slots.machine.host'),

                          subqueryload('interfaces'),
                          lazyload('interfaces.hardware_entity'),
                          joinedload('interfaces.assignments'),
                          joinedload('interfaces.assignments.network'),
                          joinedload('interfaces.assignments.dns_records'))

        # Prefer the primary name for ordering
        q = q.outerjoin(DnsRecord, (Fqdn, DnsRecord.fqdn_id == Fqdn.id),
                        DnsDomain)
        q = q.options(contains_eager('primary_name'),
                      contains_eager('primary_name.fqdn'),
                      contains_eager('primary_name.fqdn.dns_domain'))
        q = q.order_by(Fqdn.name, DnsDomain.name, Chassis.label)
        if fullinfo:
            return q.all()
        else:
            return StringAttributeList(q.all(), "fqdn")
