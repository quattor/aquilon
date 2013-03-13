# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013  Contributor
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

from sqlalchemy import Integer, Column, ForeignKey
from sqlalchemy.orm import relation, backref

from aquilon.aqdb.model import Resource, AddressAssignment, ARecord

_TN = 'service_address'
_ABV = 'srv_addr'


class ServiceAddress(Resource):
    """ Service address resources """
    __tablename__ = _TN
    __mapper_args__ = {'polymorphic_identity': _TN}
    _class_label = 'Service Address'

    resource_id = Column(Integer, ForeignKey('resource.id',
                                             name='%s_resource_fk' % _ABV),
                         primary_key=True)

    # This is not normalized, as we could get the same object by
    # self.assignments[0].dns_records[0], but this way it's faster
    dns_record_id = Column(Integer, ForeignKey('a_record.dns_record_id',
                                               name='%s_arecord_fk' % _ABV),
                           nullable=False)

    assignments = relation(AddressAssignment, cascade="all, delete-orphan",
                           passive_deletes=True,
                           backref=backref('service_address'))

    dns_record = relation(ARecord, innerjoin=True,
                          backref=backref('service_address', uselist=False))

    @property
    def interfaces(self):
        ifaces = []
        for addr in self.assignments:
            if addr.interface.name not in ifaces:
                ifaces.append(addr.interface.name)

        ifaces.sort()
        return ifaces


srvaddr = ServiceAddress.__table__
srvaddr.primary_key.name = '%s_pk' % (_TN)
srvaddr.info['unique_fields'] = ['name', 'holder']
