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
""" Store the list of servers that backs a service instance."""

from datetime import datetime

from sqlalchemy import (Column, Table, Integer, Sequence, String, DateTime,
                        ForeignKey, UniqueConstraint, Index)
from sqlalchemy.orm import relation, deferred, backref
from sqlalchemy.ext.orderinglist import ordering_list

from aquilon.aqdb.model import Base, System, ServiceInstance


class ServiceInstanceServer(Base):
    """ Store the list of servers that backs a service instance."""

    __tablename__ = 'service_instance_server'

    service_instance_id = Column(Integer, ForeignKey('service_instance.id',
                                                     name='sis_si_fk',
                                                     ondelete='CASCADE'),
                                 primary_key=True)

    system_id = Column(Integer, ForeignKey('system.id',
                                           name='sis_system_fk',
                                           ondelete='CASCADE'),
                       primary_key=True)

    position = Column(Integer, nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = deferred(Column(String(255), nullable=True))

    service_instance = relation(ServiceInstance)
    system = relation(System, uselist=False, backref='sislist')

    def __str__(self):
        return str(self.system.fqdn)

    def __repr__(self):
        return self.__class__.__name__ + " " + str(self.system.fqdn)


service_instance_server = ServiceInstanceServer.__table__
service_instance_server.primary_key.name='service_instance_server_pk'

table = service_instance_server

#TODO: would we like this mapped in service_instance.py instead?
ServiceInstance.servers = relation(ServiceInstanceServer,
                          collection_class=ordering_list('position'),
                          order_by=[ServiceInstanceServer.__table__.c.position])



