#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
""" test populating campus """

import os
import sys

_DIR = os.path.dirname(os.path.realpath(__file__))
_LIBDIR = os.path.join(_DIR, "..", "..", "lib", "python2.5")

if _LIBDIR not in sys.path:
    sys.path.insert(0, _LIBDIR)

import aquilon.aqdb.depends

from aquilon.aqdb.dsdb         import DsdbConnection
from aquilon.aqdb.db_factory   import db_factory
from aquilon.aqdb.loc.building import Building
from aquilon.aqdb.loc.campus   import Campus, CampusDiffStruct

#_n   = 'ny'
#_fn  = 'New York'
_cmt = 'TEST CAMPUS'

class TestCampusPopulate(object):
    """ Tests loading a campus from dsdb """
    #TODO: explore test generators for population of ALL campuses

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
            print 'failed committing reparents\n%s'%(e)
            raise e
            return False

        temp = campus.name
        try:
            self.sess.delete(campus)
            self.sess.commit()
        except Exception, e:
            print '  FAILED CAMPUS DELETE in _clean_up(): %s'%(e)
            self.sess.close()
            return False

        self.deleted.append(temp)
        return True

    def _get_campus_csv(self):
        """ This is a cheap way to hardcode the proper name and code
            data for campus, which isn't 100% clean in dsdb. There are few
            enough of them that I've hardwired these attributes here """
        import csv
        filename = os.path.join(_DIR,'data/campus.csv')
        return csv.DictReader(open(filename, 'rb'),
                              ['code', 'name', 'country'],
                              skipinitialspace=True)

    def setUp(self,verbose=0):
        self.verbose = verbose
        self.aqdb = db_factory()
        self.sess = self.aqdb.Session()
        assert self.sess
        
        self.dsdb = DsdbConnection()
        assert self.dsdb

        self.campuses = []
        
        for row in self._get_campus_csv():
            code  = row['code']
            fname = row['name']
            cmt   = ', '.join([row['name'], row['country'], _cmt])

            #if the campus already exists, nuke it ahead of time
            c = self.sess.query(Campus).filter_by(name=code).first()
            if c:
                print 'CAMPUS exists in setup! %s %s'%(
                    code, c.sublocations)
                self._clean_up(c)
                self.sess.close()

            self.campuses.append(Campus(name=code,
                #code=code,
                                        fullname=fname,
                                        comments=cmt))
            self.deleted = []

    def tearDown(self):
        for c in self.sess.query(Campus).all():
            if not self._clean_up(c):
                print 'tearDown() %s FAILED'%(c)
        #print 'deleted %s'%(self.deleted)

    def testPopulate(self):
        for c in self.campuses:
            cs = CampusDiffStruct(self.dsdb,
                                  self.aqdb.Session(),
                                  c,
                                  verbose=self.verbose)

            assert(cs.sync(), 'CAMPUS CREATION FAILED')
            #nose.assert_true(cs.sync(), '%s CREATION FAILED'%(c))

            new_campus = self.sess.query(Campus).filter_by(name=c.name).first()

            if new_campus:
                if len(new_campus.sublocations) < 1:
                    print '  EMPTY %s: contains %s'%(new_campus, cs.buildings)
                else:
                    print 'created %s %s'%(new_campus,
                                             new_campus.sublocations)
            else:
                print 'CAMPUS %s failed'%(c.name)

#if __name__ == "__main__":
#    import sys
#
#    import ms.version
#    ms.version.addpkg('nose','0.10.3')
#    import nose
#
#    #nose.run()

#    c = testCampusLoad()0
#    c.runTest(sys.argv)

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

#def commitment_phobic(func):
#    """ Decorator any db command in try/catch """
#    try:
#        retval = func()
#        return retval
#    except Exception,e:
#        print e
#        session.rollback()
#        session.close()
#        raise
    """def test1Continents(self):
        assert(self.cs.continents)

    def test2Countries(self):
        assert(self.cs.countries)

    def test3Cities(self):
        assert(self.cs.cities)

    def test4Buildings(self):
        assert(self.cs.buildings)"""
