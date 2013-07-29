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
""" Store the list of servers that backs a service instance."""

from datetime import datetime

from sqlalchemy import (Column, Integer, String, DateTime, ForeignKey,
                        PrimaryKeyConstraint, Index)
from sqlalchemy.orm import relation, deferred, backref
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.ext.associationproxy import association_proxy

from aquilon.aqdb.model import Base, Host, ServiceInstance

_TN = 'service_instance_server'


class ServiceInstanceServer(Base):
    """ Store the list of servers that backs a service instance."""

    __tablename__ = _TN

    service_instance_id = Column(Integer, ForeignKey('service_instance.id',
                                                     name='sis_si_fk',
                                                     ondelete='CASCADE'),
                                 nullable=False)

    host_id = Column(Integer, ForeignKey('host.machine_id',
                                         name='sis_host_fk',
                                         ondelete='CASCADE'),
                     nullable=False)

    position = Column(Integer, nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = deferred(Column(String(255), nullable=True))

    service_instance = relation(ServiceInstance, innerjoin=True,
                                backref=backref("servers",
                                                cascade="all, delete-orphan",
                                                collection_class=ordering_list('position'),
                                                order_by=[position]))

    host = relation(Host, innerjoin=True,
                    backref=backref('_services_provided',
                                    cascade="all, delete-orphan"))

    __table_args__ = (PrimaryKeyConstraint(service_instance_id, host_id,
                                           name="%s_pk" % _TN),
                      Index("sis_host_idx", host_id))


def _sis_host_creator(host):
    return ServiceInstanceServer(host=host)


def _sis_si_creator(service_instance):
    return ServiceInstanceServer(service_instance=service_instance)

ServiceInstance.server_hosts = association_proxy('servers', 'host',
                                                 creator=_sis_host_creator)

Host.services_provided = association_proxy('_services_provided',
                                           'service_instance',
                                           creator=_sis_si_creator)
