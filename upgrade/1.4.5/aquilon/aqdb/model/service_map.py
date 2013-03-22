# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2013  Contributor
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
""" Maps service instances to locations. See class.__doc__ """

from datetime import datetime

from sqlalchemy import (Column, Table, Integer, Sequence, String, DateTime,
                        ForeignKey, UniqueConstraint, Index)
from sqlalchemy.orm import relation, deferred, backref

from aquilon.aqdb.model import Base, Location, ServiceInstance


class ServiceMap(Base):
    """ Service Map: mapping a service_instance to a location.
        The rows in this table assert that an instance is a valid useable
        default that clients can choose as their provider during service
        autoconfiguration. """

    __tablename__ = 'service_map'

    id = Column(Integer, Sequence('service_map_id_seq'), primary_key=True)
    service_instance_id = Column(Integer, ForeignKey('service_instance.id',
                                                name='svc_map_svc_inst_fk'),
                          nullable=False)

    location_id = Column(Integer, ForeignKey('location.id',
                                             ondelete='CASCADE',
                                             name='svc_map_loc_fk'),
                    nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                       nullable=False))
    comments = deferred(Column(String(255), nullable=True))
    location = relation(Location, backref='service_maps')
    service_instance = relation(ServiceInstance, backref='service_map',
                                passive_deletes=True)

    def _service(self):
        return self.service_instance.service
    service = property(_service)

    def __repr__(self):
        return '<Service Mapping of service %s at %s %s >'%(
            self.service_instance.service, self.location.location_type,
            self.location.name)

service_map = ServiceMap.__table__
service_map.primary_key.name='service_map_pk'

service_map.append_constraint(
    UniqueConstraint('service_instance_id', 'location_id',
                     name='svc_map_loc_inst_uk'))

table = service_map



