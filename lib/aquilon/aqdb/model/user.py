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
""" Class for maanaging User """

from datetime import datetime

from sqlalchemy import (Column, Integer, String, Sequence, Boolean, UniqueConstraint,
                        DateTime)
from sqlalchemy.orm import deferred

from aquilon.aqdb.model import Base

_TN = 'userinfo'


class User(Base):
    """ Manage Users  """
    __tablename__ = _TN
    _class_label = 'User'

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)

    # user names are case sensitive, so no AqStr here
    name = Column(String(32), nullable=False)

    uid = Column(Integer, nullable=False)
    gid = Column(Integer, nullable=False)
    full_name = Column(String(64), nullable=False)
    home_dir = Column(String(64), nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    __table_args__ = (UniqueConstraint(name, name='%s_user_uk' % _TN),)

usr = User.__table__  # pylint: disable=C0103
usr.info['unique_fields'] = ['name']
