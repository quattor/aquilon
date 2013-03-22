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
""" Country is a subclass of Location """

from sqlalchemy import Column, Integer, ForeignKey

from aquilon.aqdb.model import Location

class Country(Location):
    """ Country is a subtype of location """
    __tablename__ = 'country'
    __mapper_args__ = {'polymorphic_identity':'country'}
    id = Column(Integer,ForeignKey('location.id',
                                   name='country_loc_fk',
                                   ondelete='CASCADE'),
                primary_key=True)

country = Country.__table__
country.primary_key.name='country_pk'

table = country

def populate(sess, *args, **kw):
    if len(sess.query(Country).all()) < 1:
        from aquilon.aqdb.model import Continent, Hub

        log = kw['log']
        assert log, "no log in kwargs for Country.populate()"
        dsdb = kw['dsdb']
        assert dsdb, "No dsdb in kwargs for Country.populate()"

        cnts = {}

        for c in sess.query(Continent).all():
            cnts[c.name] = c

        for row in dsdb.dump('country'):

            a = Country(name = str(row[0]),
                        fullname = str(row[1]),
                        parent = cnts[str(row[2])])
            sess.add(a)

        sess.commit()

        try:
            sess.commit()
        except Exception, e:
            log.error(str(e))

        log.debug('created %s countries'%(len(sess.query(Country).all())))


