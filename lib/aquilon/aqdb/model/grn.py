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
""" Class for mapping GRNs to EON IDs """

from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import deferred

from aquilon.aqdb.model import (
    Base,
    HostEnvironment,
    Location,
    Parameterized,
)

_TN = 'grn'


class Grn(Base):
    """ Map GRNs to EON IDs """
    __tablename__ = _TN
    _instance_label = 'grn'
    _class_label = 'GRN'

    eon_id = Column(Integer, primary_key=True, autoincrement=False)

    # GRNs are case sensitive, so no AqStr here
    # TODO: is there a limit on the length of GRNs? 132 is the longest currently
    grn = Column(String(255), nullable=False, unique=True)

    # If False, then assigning new objects to this GRN should fail, but old
    # objects may still point to it
    disabled = Column(Boolean, nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    __table_args__ = ({'info': {'unique_fields': ['grn'],
                                'extra_search_fields': ['eon_id']}},)


class ParameterizedGrn(Parameterized):
    _objects = {
        'main': Grn,
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
