# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Contains the logic for `aq show manager --missing`."""

from sqlalchemy.orm import contains_eager

from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.formats.interface import MissingManagersList
from aquilon.aqdb.model import (Interface, AddressAssignment, HardwareEntity,
                                DnsRecord, DnsDomain, Fqdn)


class CommandShowManagerMissing(BrokerCommand):

    def render(self, session, **arguments):
        q = session.query(Interface)
        q = q.filter_by(interface_type='management')
        q = q.outerjoin(AddressAssignment)
        q = q.filter(AddressAssignment.id == None)
        q = q.reset_joinpoint()

        q = q.join(HardwareEntity)
        q = q.filter_by(hardware_type='machine')
        q = q.options(contains_eager('hardware_entity'))

        # MissingManagerList wants the fqdn, so get it in one go
        q = q.outerjoin(DnsRecord, (Fqdn, DnsRecord.fqdn_id == Fqdn.id),
                        DnsDomain)
        q = q.options(contains_eager('hardware_entity.primary_name'))
        q = q.options(contains_eager('hardware_entity.primary_name.fqdn'))
        q = q.options(contains_eager('hardware_entity.primary_name.fqdn.dns_domain'))

        # Order by FQDN if it exists, otherwise fall back to the label
        q = q.order_by(Fqdn.name, DnsDomain.name, HardwareEntity.label)
        return MissingManagersList(q.all())
