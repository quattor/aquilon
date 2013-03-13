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
""" Building is a subclass of Location """
from sqlalchemy import Column, Integer, ForeignKey

from aquilon.aqdb.model import Location


class Building(Location):
    """ Building is a subtype of location """
    __tablename__ = 'building'
    __mapper_args__ = {'polymorphic_identity' : 'building'}

    id = Column(Integer, ForeignKey('location.id',
                                    name='building_loc_fk',
                                    ondelete='CASCADE'),
                primary_key=True)

building = Building.__table__
building.primary_key.name='building_pk'

table = building

def populate(sess, *args, **kw):

    if len(sess.query(Building).all()) > 0:
        return

    from aquilon.aqdb.model import City

    log = kw['log']
    assert log, "no log in kwargs for Building.populate()"
    dsdb = kw['dsdb']
    assert dsdb, "No dsdb in kwargs for Building.populate()"

    city = {}
    for c in sess.query(City).all():
        city[c.name] = c

    for row in dsdb.dump('building'):
        try:
            p = city[str(row[2])]
        except KeyError, e:
            log.error(str(e))
            continue

        a = Building(name = str(row[0]),
                    fullname = str(row[1]),
                    parent = city[str(row[2])])
        sess.add(a)
    sess.commit()
    log.debug('created %s buildings'%(len(sess.query(Building).all())))



