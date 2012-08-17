# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010,2011,2012  Contributor
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
""" Personality as a high level cfg object """
from datetime import datetime

from sqlalchemy import (Column, Integer, Boolean, DateTime, Sequence, String,
                        ForeignKey, UniqueConstraint, Index)
from sqlalchemy.orm import relation, deferred

from aquilon.aqdb.model import Base, Archetype, Grn
from aquilon.aqdb.column_types.aqstr import AqStr

_ABV = 'prsnlty'
_TN = 'personality'

_PGN = 'personality_grn_map'
_PGNABV = 'pers_grn_map'


class Personality(Base):
    """ Personality names """
    __tablename__ = _TN

    id = Column(Integer, Sequence('%s_seq' % (_ABV)), primary_key=True)
    name = Column(AqStr(32), nullable=False)
    archetype_id = Column(Integer, ForeignKey(
        'archetype.id', name='%s_arch_fk' % (_ABV)), nullable=False)

    cluster_required = Column(Boolean(name="%s_clstr_req_ck" % _TN),
                              default=False, nullable=False)

    config_override = Column(Boolean(name="persona_cfg_override_ck"),
                          default=False, nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = Column(String(255), nullable=True)

    archetype = relation(Archetype)

    @property
    def is_cluster(self):
        return self.archetype.cluster_type is not None

    def __format__(self, format_spec):
        instance = "%s/%s" % (self.archetype.name, self.name)
        return self.format_helper(format_spec, instance)


personality = Personality.__table__   # pylint: disable=C0103

personality.primary_key.name = '%s_pk' % _ABV
personality.append_constraint(UniqueConstraint('name', 'archetype_id',
                                               name='%s_uk' % _TN))
personality.info['unique_fields'] = ['name', 'archetype']

Index('%s_arch_idx' % _ABV, personality.c.archetype_id)


class PersonalityGrnMap(Base):
    __tablename__ = _PGN

    personality_id = Column(Integer, ForeignKey('%s.id' % _TN,
                                                name='%s_personality_fk' % _PGNABV),
                            primary_key=True)

    eon_id = Column(Integer, ForeignKey('grn.eon_id',
                                        name='%s_grn_fk' % _PGNABV),
                    primary_key=True)

    personality = relation(Personality)
    grn = relation(Grn)


pgn = PersonalityGrnMap.__table__  # pylint: disable=C0103
pgn.primary_key.name = '%s_pk' % _PGN

Personality.grns = relation(Grn, secondary=PersonalityGrnMap.__table__)
