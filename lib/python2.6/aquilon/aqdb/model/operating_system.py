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
""" Operating System as a high level cfg object """
from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, ForeignKey,
                        UniqueConstraint)
from sqlalchemy.orm import relation, deferred

from aquilon.aqdb.model import Base, Archetype
from aquilon.aqdb.column_types.aqstr import AqStr

_TN = 'operating_system'
_ABV = 'os'


class OperatingSystem(Base):
    """ Operating Systems """
    __tablename__ = _TN
    _class_label = 'Operating System'

    id = Column(Integer, Sequence('%s_seq' % _ABV), primary_key=True)
    name = Column(AqStr(32), nullable=False)
    version = Column(AqStr(16), nullable=False)
    archetype_id = Column(Integer, ForeignKey('archetype.id',
                                              name='%s_arch_fk' % _ABV,
                                              ondelete="CASCADE"),
                          nullable=False)
    #vendor id?
    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = Column(String(255), nullable=True)

    archetype = relation(Archetype, lazy=False, innerjoin=True)

    __table_args__ = (UniqueConstraint(archetype_id, name, version,
                                       name='%s_arch_name_version_uk' % _ABV),)

    def __format__(self, format_spec):
        instance = "%s/%s-%s" % (self.archetype.name, self.name, self.version)
        return self.format_helper(format_spec, instance)

    @property
    def cfg_path(self):
        return 'os/%s/%s' % (self.name, self.version)

operating_system = OperatingSystem.__table__  # pylint: disable=C0103
operating_system.info['unique_fields'] = ['name', 'version', 'archetype']
