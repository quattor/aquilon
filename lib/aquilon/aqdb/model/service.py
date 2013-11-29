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
""" The module governing tables and objects that represent what are known as
    Services (defined below) in Aquilon.

    Many important tables and concepts are tied together in this module,
    which makes it a bit larger than most. Additionally there are many layers
    at work for things, especially for Host, Service Instance, and Map. The
    reason for this is that breaking each component down into seperate tables
    yields higher numbers of tables, but with FAR less nullable columns, which
    simultaneously increases the density of information per row (and speedy
    table scans where they're required) but increases the 'thruthiness'[1] of
    every row. (Daqscott 4/13/08)

    [1] http://en.wikipedia.org/wiki/Truthiness """

from datetime import datetime

from sqlalchemy import (Column, Integer, Sequence, String, DateTime, Boolean,
                        ForeignKey, UniqueConstraint, PrimaryKeyConstraint,
                        Index)
from sqlalchemy.orm import relation, backref, deferred, aliased, object_session
from sqlalchemy.sql import or_
from sqlalchemy.util import memoized_property

from aquilon.aqdb.column_types.aqstr import AqStr
from aquilon.aqdb.model import Base, Archetype, Personality

_TN = 'service'
_SLI = 'service_list_item'
_PSLI = 'personality_service_list_item'
_ABV = 'prsnlty_sli'


class Service(Base):
    """ SERVICE: composed of a simple name of a service consumable by
        OTHER hosts. Applications that run on a system like ssh are
        personalities or features, not services. """

    __tablename__ = _TN

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)
    name = Column(AqStr(64), nullable=False)
    max_clients = Column(Integer, nullable=True)  # 0 means 'no limit'
    need_client_list = Column(Boolean(name='%s_need_client_list_ck' % _TN),
                              nullable=False, default=True)
    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = Column(String(255), nullable=True)

    __table_args__ = (UniqueConstraint(name, name='svc_name_uk'),)

    @memoized_property
    def cluster_aligned_personalities(self):
        session = object_session(self)

        PersService = aliased(Service)
        ArchService = aliased(Service)

        # Check if the service instance is used by any cluster-bound personality
        q = session.query(Personality.id)
        q = q.outerjoin(PersService, Personality.services)
        q = q.reset_joinpoint()
        q = q.join(Archetype).filter(Archetype.cluster_type != None)
        q = q.outerjoin(ArchService, Archetype.services)
        q = q.filter(or_(PersService.id == self.id, ArchService.id == self.id))
        return [pers.id for pers in q]

service = Service.__table__  # pylint: disable=C0103
service.info['unique_fields'] = ['name']


class ServiceListItem(Base):
    """ Service list item is an individual member of a service list, defined
        in configuration. They represent requirements for baseline archetype
        builds. Think of things like 'dns', 'syslog', etc. that you'd need just
        to get a host up and running...that's what these represent. """

    __tablename__ = _SLI
    _class_label = 'Required Service'

    service_id = Column(Integer, ForeignKey('%s.id' % (_TN),
                                            name='sli_svc_fk',
                                            ondelete='CASCADE'),
                        nullable=False)

    archetype_id = Column(Integer, ForeignKey('archetype.id',
                                              name='sli_arctype_fk',
                                              ondelete='CASCADE'),
                          nullable=False)

    __table_args__ = (PrimaryKeyConstraint(service_id, archetype_id,
                                           name="%s_pk" % _SLI),
                      Index('srvlst_archtyp_idx', archetype_id))

Service.archetypes = relation(Archetype, secondary=ServiceListItem.__table__,
                              backref=backref("services"))


class PersonalityServiceListItem(Base):
    """ A personality service list item is an individual member of a list
       of required services for a given personality. They represent required
       services that need to be assigned/selected in order to build
       hosts in said personality """

    __tablename__ = _PSLI

    service_id = Column(Integer, ForeignKey('%s.id' % (_TN),
                                            name='%s_svc_fk' % (_ABV),
                                            ondelete='CASCADE'),
                        nullable=False)

    personality_id = Column(Integer, ForeignKey('personality.id',
                                                name='sli_prsnlty_fk',
                                                ondelete='CASCADE'),
                            nullable=False)

    __table_args__ = (PrimaryKeyConstraint(service_id, personality_id,
                                           name="%s_pk" % _ABV),
                      Index('%s_prsnlty_idx' % _ABV, personality_id))

Service.personalities = relation(Personality,
                                 secondary=PersonalityServiceListItem.__table__,
                                 backref=backref("services"))
