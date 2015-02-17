# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013,2014  Contributor
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

from sqlalchemy import Column, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import relation, backref

from aquilon.aqdb.model import Base, Resource, ARecord, Interface

_TN = 'service_address'


class ServiceAddress(Resource):
    """ Service address resources """
    __tablename__ = _TN
    _class_label = 'Service Address'

    resource_id = Column(ForeignKey(Resource.id), primary_key=True)

    dns_record_id = Column(ForeignKey(ARecord.dns_record_id),
                           nullable=False, unique=True)

    dns_record = relation(ARecord, innerjoin=True,
                          backref=backref('service_address', uselist=False,
                                          passive_deletes=True))

    __table_args__ = ({'info': {'unique_fields': ['name', 'holder']}},)
    __mapper_args__ = {'polymorphic_identity': _TN}

    @property
    def ip(self):
        return self.dns_record.ip

    @property
    def network(self):
        return self.dns_record.network

    @property
    def network_environment(self):
        return self.dns_record.network.network_environment


class __ServiceAddressInterface(Base):
    __tablename__ = 'service_address_interface'

    service_address_id = Column(ForeignKey(ServiceAddress.resource_id,
                                           ondelete='CASCADE'),
                                nullable=False)

    interface_id = Column(ForeignKey(Interface.id), nullable=False, index=True)

    __table_args__ = (PrimaryKeyConstraint(service_address_id, interface_id),)

ServiceAddress.interfaces = relation(Interface,
                                     secondary=__ServiceAddressInterface.__table__,
                                     passive_deletes=True,
                                     backref=backref('service_addresses'))
