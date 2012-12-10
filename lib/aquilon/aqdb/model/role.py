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
""" Contains tables and objects for authorization in Aquilon """
from datetime import datetime

from sqlalchemy import (Column, Integer, String, DateTime, Sequence,
                        UniqueConstraint)
from sqlalchemy.orm import deferred

from aquilon.aqdb.model import Base
from aquilon.aqdb.column_types.aqstr import AqStr

_TN = 'role'


class Role(Base):
    __tablename__ = _TN

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)

    name = Column(AqStr(32), nullable=False)

    creation_date = deferred(Column(DateTime, nullable=False,
                                    default=datetime.now))

    comments = deferred(Column(String(255), nullable=True))

    __table_args__ = (UniqueConstraint(name, name='role_uk'),)

role = Role.__table__  # pylint: disable=C0103
role.primary_key.name = '%s_pk' % _TN
role.info['unique_fields'] = ['name']
