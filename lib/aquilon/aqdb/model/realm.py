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
""" Enumerates kerberos realms """
from datetime import datetime

from sqlalchemy import (Column, Integer, String, DateTime, Sequence,
                        UniqueConstraint)
from sqlalchemy.orm import deferred

from aquilon.aqdb.model import Base

#Upfront Design Decisions:
#  -Needs it's own creation_date + comments columns. Audit log depends on
#   this table for it's info, and would have a circular dependency


class Realm(Base):
    """ Represent Kerberos Realms (simple names) """
    __tablename__ = 'realm'

    id = Column(Integer, Sequence('realm_id_seq'), primary_key=True)
    name = Column(String(32), nullable=False)
    creation_date = deferred(Column(DateTime, nullable=False,
                                    default=datetime.now))
    comments = deferred(Column(String(255), nullable=True))

    __table_args__ = (UniqueConstraint(name, name='realm_uk'),)

realm = Realm.__table__  # pylint: disable=C0103
realm.info['unique_fields'] = ['name']
