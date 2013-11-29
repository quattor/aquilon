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
""" Archetype specifies the metaclass of the build """

from datetime import datetime
from sqlalchemy import (Column, Integer, DateTime, Sequence, String,
                        UniqueConstraint, Boolean)
from sqlalchemy.orm import deferred

from aquilon.aqdb.model import Base
from aquilon.aqdb.column_types import AqStr

_TN = 'archetype'


class Archetype(Base):
    """ Archetype names """
    __tablename__ = _TN

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)

    name = Column(AqStr(32), nullable=False)
    outputdesc = Column(String(255), nullable=True)

    is_compileable = Column(Boolean(name="%s_is_compileable_ck" % _TN),
                            default=False, nullable=False)

    cluster_type = Column(AqStr(32), nullable=True)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    comments = deferred(Column(String(255), nullable=True))

    __table_args__ = (UniqueConstraint(name, name='%s_uk' % _TN),)

archetype = Archetype.__table__  # pylint: disable=C0103
archetype.info['unique_fields'] = ['name']
