# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2013  Contributor
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
from sqlalchemy import (Column, Integer, DateTime, Sequence, String, ForeignKey,
                        UniqueConstraint, Boolean)
from sqlalchemy.orm import relation, deferred

from aquilon.aqdb.model import Base
from aquilon.aqdb.column_types.aqstr import AqStr

_ABV = 'archetype'


class Archetype(Base):
    """ Archetype names """
    __tablename__  = _ABV

    id = Column(Integer, Sequence('%s_id_seq'%(_ABV)), primary_key=True)
    name = Column(AqStr(32), nullable=False)
    is_compileable = Column(Boolean, default=False, nullable=False)
    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = deferred(Column(String(255), nullable=True))

archetype = Archetype.__table__
table = Archetype.__table__

archetype.primary_key.name='%s_pk'%(_ABV)
archetype.append_constraint(UniqueConstraint('name',name='%s_uk'%(_ABV)))

def populate(sess, *args, **kw):
    if len(sess.query(Archetype).all()) > 0:
        return

    for a_name in ['aquilon', 'windows', 'aurora', 'aegis', 'vmhost']:
        a = Archetype(name=a_name)
        sess.add(a)
        if a_name in ['aquilon', 'vmhost']:
            a.is_compileable = True

    try:
        sess.commit()
    except Exception, e:
        sess.rollback()
        raise e

    a = sess.query(Archetype).first()
    assert(a)


