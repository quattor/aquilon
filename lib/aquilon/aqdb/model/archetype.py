# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008-2014,2016,2018  Contributor
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
""" Archetype specifies the metaclass of the build """

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, Sequence, String, Boolean
from sqlalchemy.orm import deferred

from aquilon.exceptions_ import UnimplementedError
from aquilon.aqdb.model import (
    Base,
    HostEnvironment,
    Location,
    Parameterized,
)
from aquilon.aqdb.column_types import AqStr

_TN = 'archetype'


class Archetype(Base):
    """ Archetype names """
    __tablename__ = _TN

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)

    name = Column(AqStr(32), nullable=False, unique=True)
    outputdesc = Column(String(255), nullable=True)

    is_compileable = Column(Boolean, default=False, nullable=False)

    cluster_type = Column(AqStr(32), nullable=True)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    comments = deferred(Column(String(255), nullable=True))

    __table_args__ = ({'info': {'unique_fields': ['name']}},)

    def require_compileable(self, msg):
        if not self.is_compileable:
            raise UnimplementedError("{0} is not compileable, {1!s}."
                                     .format(self, msg))


class ParameterizedArchetype(Parameterized):
    _objects = {
        'main': Archetype,
        'host_environment': HostEnvironment,
        'location': Location,
    }

    @property
    def resholder(self):
        for resholder in self._main.resholders:
            if resholder.host_environment == self.host_environment and \
                    resholder.location == self.location:
                return resholder
        return None
