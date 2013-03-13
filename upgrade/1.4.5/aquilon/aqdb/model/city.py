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
""" City is a subclass of Location """
from sqlalchemy import Column, Integer, ForeignKey

from aquilon.aqdb.model import Location
from aquilon.aqdb.column_types.aqstr import AqStr

class City(Location):
    """ City is a subtype of location """
    __tablename__ = 'city'
    __mapper_args__ = {'polymorphic_identity' : 'city'}
    id = Column(Integer, ForeignKey('location.id',
                                    name='city_loc_fk',
                                    ondelete='CASCADE'),
                primary_key=True)
    timezone = Column(AqStr(64), nullable=True, default = 'TZ = FIX ME')

city = City.__table__
city.primary_key.name='city_pk'

table = city

def populate(sess, *args, **kw):

    if len(sess.query(City).all()) < 1:
        from aquilon.aqdb.model import Country

        log = kw['log']
        assert log, "no log in kwargs for City.populate()"
        dsdb = kw['dsdb']
        assert dsdb, "No dsdb in kwargs for City.populate()"

        cntry= {}
        for c in sess.query(Country).all():
            cntry[c.name] = c

        for row in dsdb.dump('city'):
            try:
                p = cntry[str(row[2])]
            except KeyError, e:
                log.error('couldnt find country %s'%(str(row[2])))
                continue

            a = City(name = str(row[0]),
                        fullname = str(row[1]),
                        parent = p)
            sess.add(a)

        sess.commit()



