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
""" test populating campus """

import os
import logging

from utils import load_classpath
load_classpath()

from aquilon.aqdb.model import Building, Campus, Continent
from aquilon.aqdb.model.campus import CampusDiffStruct

_cmt = 'TEST CAMPUS'

class TestCampusPopulate(object):
    """ Tests loading a campus from dsdb """

    def __init__(self, sess, *args, **kw):
        self.dsdb = kw['dsdb']
        assert self.dsdb

        self.log = logging.getLogger('aqdb.populate')

        self.sess     = sess
        self.campuses = []
        self.deleted  = []
        self.debug    = kw.pop('debug', False)

    def _reparent(self, child):
        child.parent = child.parent.parent
        self.sess.add(child)

    def _clean_up(self, campus):
        """ D.R.Y. utility. Do we need base class for location tests that do
            this business of clean up/reparenting in general? """

        #NOTE THE USE OF [:] -> you're actually modifying the list WHILE you
        #iterate, and cascades can occur. Using the slice operator fixes it
        map(self._reparent, campus.sublocations[:])

        try:
            self.sess.flush()
        except Exception, e:
            self.sess.rollback()
            self.log.error('failed committing reparents\n%s'%(e))
            raise e

        temp = campus.name
        try:
            self.sess.delete(campus)
            self.sess.commit()
        except Exception, e:
            self.log.error('  FAILED CAMPUS DELETE in _clean_up(): %s'%(e))
            self.sess.rollback()
            return False

        self.deleted.append(temp)
        return True

    def _get_campus_csv(self):
        """ This is a cheap way to hardcode the proper name and code
            data for campus, which isn't 100% clean in dsdb. There are few
            enough of them that I've hardwired these attributes here """
        import csv
        filename = os.path.join(os.path.dirname(__file__), 'data/campus.csv')
        return csv.DictReader(open(filename, 'rb'),
                              ['code', 'name', 'country'],
                              skipinitialspace=True)

    def setUp(self):
        no_continents = len(self.sess.query(Continent).all())
        if  no_continents < 4:
            self.log.error('Not enough continents (found %s)')
            return False

        for row in self._get_campus_csv():
            code  = row['code']
            fname = row['name']

            c = self.sess.query(Campus).filter_by(name=code).first()
            if c:
                continue

            self.campuses.append(Campus(name=code,
                                        #code=code,
                                        fullname=fname))
                                        #comments=cmt))

    def tearDown(self):
        for c in self.sess.query(Campus).all():
            if not self._clean_up(c):
                self.log.info('tearDown() %s FAILED'%(c))

    def testPopulate(self):
        for c in self.campuses:
            #hack for an empty campus
            #if c.name == 'at':
            #    continue

            cs = CampusDiffStruct(self.dsdb,
                                  self.sess,
                                  c)
            assert cs.sync(), 'CAMPUS CREATION FAILED'

            new_campus = self.sess.query(Campus).filter_by(name=c.name).first()

            if new_campus:
                if len(new_campus.sublocations) < 1:
                    self.log.debug('  EMPTY %s: contains %s'%(new_campus, cs.buildings))

            else:
                self.log.error('CAMPUS %s failed'%(c.name))
