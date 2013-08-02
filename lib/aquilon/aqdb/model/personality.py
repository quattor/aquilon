# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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
""" Personality as a high level cfg object """
from datetime import datetime
import re

from sqlalchemy import (Column, Integer, Boolean, DateTime, Sequence, String,
                        ForeignKey, UniqueConstraint, PrimaryKeyConstraint)
from sqlalchemy.orm import relation, backref, deferred
from sqlalchemy.inspection import inspect
from sqlalchemy.ext.associationproxy import association_proxy

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.column_types.aqstr import AqStr
from aquilon.aqdb.model import Base, Archetype, Grn, HostEnvironment

_ABV = 'prsnlty'
_TN = 'personality'

_PGN = 'personality_grn_map'
_PGNABV = 'pers_grn_map'

def _pgm_creator(tuple):
    return PersonalityGrnMap(personality=tuple[0], grn=tuple[1], target=tuple[2])


class Personality(Base):
    """ Personality names """
    __tablename__ = _TN

    id = Column(Integer, Sequence('%s_seq' % _ABV), primary_key=True)
    name = Column(AqStr(32), nullable=False)
    archetype_id = Column(Integer, ForeignKey('archetype.id',
                                              name='%s_arch_fk' % _ABV),
                          nullable=False)

    cluster_required = Column(Boolean(name="%s_clstr_req_ck" % _TN),
                              default=False, nullable=False)

    config_override = Column(Boolean(name="persona_cfg_override_ck"),
                             default=False, nullable=False)

    owner_eon_id = Column(Integer, ForeignKey('grn.eon_id',
                                              name='%s_owner_grn_fk' % _TN),
                          nullable=False)

    host_environment_id = Column(Integer, ForeignKey('host_environment.id',
                                                     name='host_environment_fk'),
                                 nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = Column(String(255), nullable=True)

    archetype = relation(Archetype, innerjoin=True)
    owner_grn = relation(Grn, innerjoin=True)
    grns = association_proxy('_grns', 'grn', creator=_pgm_creator)

    host_environment = relation(HostEnvironment, innerjoin=True)

    __table_args__ = (UniqueConstraint(archetype_id, name,
                                       name='%s_arch_name_uk' % _TN),)

    @property
    def is_cluster(self):
        return self.archetype.cluster_type is not None

    def __format__(self, format_spec):
        instance = "%s/%s" % (self.archetype.name, self.name)
        return self.format_helper(format_spec, instance)

    @classmethod
    def validate_env_in_name(cls, name, host_environment):
        env_mapper = inspect(HostEnvironment)
        persona_env = re.search("[-/](" +
                                "|".join(env_mapper.polymorphic_map.keys()) +
                                ")$", name, re.IGNORECASE)
        if persona_env and (persona_env.group(1) != host_environment):
            raise ArgumentError("Environment value in personality name '{0}' "
                                "does not match the host environment '{1}'"
                                .format(name, host_environment))

personality = Personality.__table__   # pylint: disable=C0103
personality.info['unique_fields'] = ['name', 'archetype']


class PersonalityGrnMap(Base):
    __tablename__ = _PGN

    personality_id = Column(Integer, ForeignKey('%s.id' % _TN,
                                                name='%s_personality_fk' % _PGNABV,
                                                ondelete='CASCADE'),
                            nullable=False)

    eon_id = Column(Integer, ForeignKey('grn.eon_id',
                                        name='%s_grn_fk' % _PGNABV),
                    nullable=False)

    personality = relation(Personality, innerjoin=True,
                     backref=backref('_grns', cascade='all, delete-orphan',
                                     passive_deletes=True))

    grn = relation(Grn, lazy=False, innerjoin=True,
                   backref=backref('_personalities', passive_deletes=True))

    target = Column(AqStr(32), nullable=False)

    __table_args__ = (PrimaryKeyConstraint(personality_id, eon_id, target),)

    # used by unmap
    @property
    def mapped_object(self):
        return self.personality
