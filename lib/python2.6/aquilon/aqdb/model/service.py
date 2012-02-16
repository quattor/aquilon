# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
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

from sqlalchemy import (Column, Integer, Sequence, String, DateTime, ForeignKey,
                        UniqueConstraint, Index)
from sqlalchemy.orm import relation, backref, deferred
from sqlalchemy.ext.associationproxy import association_proxy

from aquilon.aqdb.model import Base, Archetype, Personality
from aquilon.aqdb.column_types.aqstr import AqStr

_TN = 'service'
_SLI = 'service_list_item'
_PSLI = 'personality_service_list_item'
_ABV = 'prsnlty_sli'


def _service_archetype_creator(archetype):
    """ creator function for ServiceItemList """
    return ServiceListItem(archetype=archetype)


def _service_personality_creator(personality):
    """ creator function for ServiceItemList """
    return PersonalityServiceListItem(personality=personality)


class Service(Base):
    """ SERVICE: composed of a simple name of a service consumable by
        OTHER hosts. Applications that run on a system like ssh are
        personalities or features, not services. """

    __tablename__ = _TN

    id = Column(Integer, Sequence('service_id_seq'), primary_key=True)
    name = Column(AqStr(64), nullable=False)
    max_clients = Column(Integer, nullable=True)  # 0 means 'no limit'
    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments = Column(String(255), nullable=True)

    archetypes = association_proxy('_archetypes', 'archetype',
                                   creator=_service_archetype_creator)
    personalities = association_proxy('_personalities', 'personality',
                                      creator=_service_personality_creator)

    aligned_cluster_types = association_proxy('_clusters', 'cluster_type')

    @property
    def cfg_path(self):
        return 'service/%s' % (self.name)

service = Service.__table__  # pylint: disable=C0103, E1101

service.primary_key.name = 'service_pk'
service.append_constraint(UniqueConstraint('name', name='svc_name_uk'))
service.info['unique_fields'] = ['name']


class ServiceListItem(Base):
    """ Service list item is an individual member of a service list, defined
        in configuration. They represent requirements for baseline archetype
        builds. Think of things like 'dns', 'syslog', etc. that you'd need just
        to get a host up and running...that's what these represent. """

    __tablename__ = _SLI
    _class_label = 'Required Service'

    id = Column(Integer, Sequence('service_list_item_id_seq'),
                           primary_key=True)

    service_id = Column(Integer, ForeignKey('%s.id' % (_TN),
                                            name='sli_svc_fk',
                                            ondelete='CASCADE'),
                        nullable=False)

    archetype_id = Column(Integer, ForeignKey('archetype.id',
                                              name='sli_arctype_fk',
                                              ondelete='CASCADE'),
                          nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = deferred(Column(String(255), nullable=True))

    archetype = relation(Archetype, uselist=False, lazy=False, innerjoin=True,
                         backref=backref('_services',
                                         cascade='all, delete-orphan'))
    service = relation(Service, uselist=False, lazy=False, innerjoin=True,
                       backref=backref('_archetypes',
                                       cascade='all, delete-orphan'))

sli = ServiceListItem.__table__  # pylint: disable=C0103, E1101
sli.primary_key.name = 'svc_list_item_pk'
sli.append_constraint(UniqueConstraint('archetype_id', 'service_id',
                                       name='svc_list_svc_uk'))
sli.info['unique_fields'] = ['archetype', 'service']

Index('srvlst_archtyp_idx', sli.c.archetype_id)


class PersonalityServiceListItem(Base):
    """ A personality service list item is an individual member of a list
       of required services for a given personality. They represent required
       services that need to be assigned/selected in order to build
       hosts in said personality """

    __tablename__ = _PSLI

    service_id = Column(Integer, ForeignKey('%s.id' % (_TN),
                                               name='%s_svc_fk' % (_ABV),
                                               ondelete='CASCADE'),
                           primary_key=True)

    personality_id = Column(Integer, ForeignKey('personality.id',
                                                 name='sli_prsnlty_fk',
                                                 ondelete='CASCADE'),
                             primary_key=True)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = deferred(Column(String(255), nullable=True))

    personality = relation(Personality, uselist=False, lazy=False,
                           innerjoin=True,
                           backref=backref('_services',
                                           cascade='all, delete-orphan'))
    service = relation(Service, uselist=False, lazy=False, innerjoin=True,
                       backref=backref('_personalities',
                                       cascade='all, delete-orphan'))

psli = PersonalityServiceListItem.__table__  # pylint: disable=C0103, E1101
psli.primary_key.name = '%s_pk' % _ABV
psli.info['unique_fields'] = ['personality', 'service']

Index('%s_prsnlty_idx' % _ABV, psli.c.personality_id)
