# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009-2014,2016,2019  Contributor
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

from aquilon.aqdb.model import Base, Archetype, AssetLifecycle
from aquilon.aqdb.column_types.aqstr import AqStr

_TN = 'operating_system'


class OperatingSystem(Base):
    """ Operating Systems """
    __tablename__ = _TN
    _class_label = 'Operating System'

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)
    name = Column(AqStr(32), nullable=False)
    version = Column(AqStr(32), nullable=False)
    archetype_id = Column(ForeignKey(Archetype.id, ondelete="CASCADE"),
                          nullable=False)
    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = Column(String(255), nullable=True)

    lifecycle_id = Column(ForeignKey(AssetLifecycle.id), nullable=False)

    archetype = relation(Archetype, lazy=False, innerjoin=True)

    lifecycle = relation(AssetLifecycle, innerjoin=True)

    __table_args__ = (UniqueConstraint(archetype_id, name, version),
                      {'info': {'unique_fields': ['name', 'version',
                                                  'archetype']}})

    def __format__(self, format_spec):
        instance = "%s/%s-%s" % (self.archetype.name, self.name, self.version)
        return self.format_helper(format_spec, instance)
