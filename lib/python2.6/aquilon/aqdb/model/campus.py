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
""" Campus is a subclass of Location """
import warnings

from sqlalchemy import Column, Integer, ForeignKey

from aquilon.aqdb.model import Location, Building


class Campus(Location):
    """ Campus is a subtype of location """
    __tablename__ = 'campus'
    __mapper_args__ = {'polymorphic_identity': 'campus'}

    id = Column(Integer, ForeignKey('location.id',
                                    name='campus_loc_fk',
                                    ondelete='CASCADE'),
                primary_key=True)


campus = Campus.__table__  # pylint: disable=C0103
campus.primary_key.name = 'campus_pk'
campus.info['unique_fields'] = ['name']


class CampusDiffStruct(object):  # pragma: no cover
    """ Handy for populating campuses and finding common parent for
        sublocation structural elements within """

    def __init__(self, dsdb, sess, campus_obj, verbose=0, *args, **kw):
        """ accepts dsdb connection for flexible dependency injection """
        self.dsdb = dsdb
        self.sess = sess
        self.co = campus_obj
        self.verbose = verbose
        self.data = {}

        building_names = map(lambda x: x[0],
                             dsdb.dump('buildings_by_campus',
                                       campus=self.co.name))

        if len(building_names) < 1:
            msg = "No buildings found for campus '%s'" % self.co.name
            warnings.warn(msg)

        query = self.sess.query(Building)
        self.buildings = query.filter(Location.name.in_(building_names)).all()

        self.data['cities'] = []
        self.data['countries'] = []
        self.data['continents'] = []

        for bldg in self.buildings:
            #checking for None here b/c error conditions make that possible
            if bldg.city is not None:
                self.data['cities'].append(bldg.city)

            if bldg.country is not None:
                self.data['countries'].append(bldg.country)

            #put the is not None into my_set class
            if bldg.continent is not None:
                self.data['continents'].append(bldg.continent)

        for (key, val) in self.data.iteritems():
            self.data[key] = set(val)

    def __repr__(self):
        return '<Campus Struct: name = %s, code = %s, comments = %s >' % (
            self.co.name, self.co.code, self.co.comments)

    def _dbg(self, level, msg):
        if self.verbose >= level:
            print msg

    def _validate(self):
        if len(self.data['continents']) <= 0:
            msg = "No continents found for %s" % self.co
            raise ValueError(msg)

        elif len(self.data['countries']) <= 0:
            msg = "No countries found for %s" % self.co
            raise ValueError(msg)

        elif len(self.data['cities']) <= 0:
            msg = "No cities found for campus '%s'" % self.co
            raise ValueError(msg)

        elif len(self.data['continents']) > 1:
            #we span continents, raise a BIG alarm!
            #TODO: give error message useful diagnostic info:
            # campus code plus the buildings and continents you found.
            msg = "ERROR: Campus %s with %s. Continents aren't to be spanned" % (
                self.co, self.data['continents'])
            raise ValueError(msg)

    def sync(self):
        self._validate()

        for atrb in ['countries', 'cities']:
            #if we've hit cities, we can go no farther, so reparent it.
            #logic changes if we need more than one campus per city.
            #this is currently allowable but highly unlikely in dsdb

            if len(self.data[atrb]) > 1 or (
                len(self.data[atrb]) == 1 and atrb == 'cities'):

                self._dbg(3, 'Have to reparent %s %s' % (atrb, self.data[atrb]))

                self.data[atrb] = list(self.data[atrb])
                self.co.parent = self.data[atrb][0].parent

                self._dbg(3, 'campus parent is now set to %s' % self.co.parent)

                try:
                    self.sess.add(self.co)
                    self.sess.flush()
                except Exception, e:
                    print 'ERROR commiting new campus parent: %s' % e
                    self.sess.close()
                    return False

                for subloc in self.data[atrb]:
                    subloc.parent = self.co
                    msg = '%s parent now set to %s' % (subloc, self.co)
                    self._dbg(3, msg)
                    self.sess.add(subloc)

                self._dbg(3, 'commiting changes to sublocs %s' % self.data[atrb])

                try:
                    self.sess.commit()
                except Exception, e:
                    print 'rolling back in sync()\n%s' % e
                    self.sess.close()
                    return False

                return True

        else:
            #this *should* be caught by _verify() anyway.
            msg = "No valid interpretation for campus %s" % self.co.name
            raise ValueError(msg)
