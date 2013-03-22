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
""" see class.__doc__ for description """

from datetime import datetime

from sqlalchemy import (Column, Table, Integer, Sequence, String, DateTime,
                        ForeignKey, UniqueConstraint, Index)
from sqlalchemy.orm import relation, deferred, backref

from aquilon.aqdb.model import Base, Host, Archetype, Service


class ServiceListItem(Base):
    """ Service list item is an individual member of a service list, defined
        in configuration. They represent requirements for baseline archetype
        builds. Think of things like 'dns', 'syslog', etc. that you'd need just
        to get a host up and running...that's what these represent. """

    __tablename__ = 'service_list_item'

    id = Column(Integer, Sequence('service_list_item_id_seq'),
                           primary_key=True)

    service_id = Column(Integer, ForeignKey('service.id',
                                            name='sli_svc_fk',
                                            ondelete='CASCADE'),
                        nullable=False)

    archetype_id = Column(Integer, ForeignKey('archetype.id',
                                              name='sli_arctype_fk',
                                              ondelete='CASCADE'),
                          nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False ))
    comments = deferred(Column(String(255), nullable=True))

    archetype = relation(Archetype, backref='service_list')
    service = relation(Service)

service_list_item = ServiceListItem.__table__
service_list_item.primary_key.name='svc_list_item_pk'
service_list_item.append_constraint(
    UniqueConstraint('archetype_id', 'service_id', name='svc_list_svc_uk'))

Index('srvlst_archtyp_idx', service_list_item.c.archetype_id)

table = service_list_item



