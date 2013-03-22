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
""" Lists of location types that define search ordering (as an algorithm).
    Intended for use with service maps during automated instance selection """
from datetime import datetime

from sqlalchemy import (Column, Integer, String, DateTime, Sequence, ForeignKey,
                        UniqueConstraint)

from sqlalchemy.orm import relation

from aquilon.aqdb.model import Base
from aquilon.aqdb.column_types.aqstr import AqStr

_ABV = 'lsl'

class LocationSearchList(Base):
    """ Lists of location types that define search ordering (as an algorithm).
    Intended for use with service maps during automated instance selection """

    __tablename__ = 'location_search_list'

    id = Column(Integer, Sequence('%s_seq'%(_ABV)), primary_key=True)

    name = Column(AqStr(32), nullable=False)

    creation_date = Column(DateTime, default=datetime.now,
                                    nullable=False )
    comments = Column(String(255), nullable=True)



location_search_list = LocationSearchList.__table__
table = LocationSearchList.__table__


location_search_list.primary_key.name='loc_search_list_pk'
location_search_list.append_constraint(
    UniqueConstraint('name', name='location_search_list_uk'))
#    UniqueConstraint('name', name='%s_uk' % (_ABV)))

def populate(sess, *args, **kw):

    if len(sess.query(LocationSearchList).all()) < 1:
        l = LocationSearchList(name='full')
        sess.add(l)

        try:
            sess.commit()
        except Exception, e:
            sess.rollback()
            raise e

    m = sess.query(LocationSearchList).first()
    assert m



