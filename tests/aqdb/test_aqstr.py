#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon
""" tests the AqStr column_type """
import sys
import os
import msversion

import unittest

if __name__ == "__main__":
    #import testing_depends
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..", "lib", "python2.5")
    sys.path.insert(0, SRCDIR)
#import nose

import aquilon.aqdb.depends
#msversion.addpkg('sqlalchemy', '0.5beta', 'dev')
#msversion.addpkg('ipython','0.8.2','dist')

import aquilon.aqdb.db_factory         as aqdbf
import aquilon.aqdb.utils.shell        as shell

from aquilon.aqdb.column_types.aqstr import AqStr

from sqlalchemy import MetaData, Table, Column, Integer, insert, create_engine
from sqlalchemy.orm import create_session
from sqlalchemy.ext.declarative import declarative_base

from exceptions import TypeError

dsn  = 'sqlite:///:memory:'
eng  = create_engine(dsn)  #, echo = True)
Base = declarative_base(engine = eng)

s    = create_session(bind = eng, transactional = True)

class StringTbl(Base):
    __tablename__ = 'aqstr_test'
    id   = Column(Integer, primary_key = True)
    name = Column(AqStr(16), nullable = False, unique = True)

    def __repr__(self):
            return self.__class__.__name__ + ' ' + str(self.name)

class testAqStr(unittest.TestCase):

    def setUp(self, *args, **kw):
        StringTbl.__table__.create()
        self.t = StringTbl.__table__

    def tearDown(self, *args, **kw):
        #in memory DB, doesn't need any tear down
        pass

    def testInsert(self):
        self.t.insert().execute(name = 'Hi there')
        o = self.t.select().execute().fetchone()
        assert o['name'].startswith('h'), 'lower case failure'

        self.t.insert().execute(name = '  some eXTRa space     ')
        p = self.t.select().execute().fetchall()[1]
        assert p['name'].startswith('s')

        print list(self.t.select().execute())

    def testObjCreate(self):
        f = StringTbl(name='  ThisISALONGTEST  ')
        print "before commit: '%s'"%(f)

        s.save(f)
        print 'setting autoexpire = True'
        s.autoexpire = True
        s.commit()
        s.autoexpire = False

        print "after commit '%s'"%(f)

        #print "table query: %s"%(s.query(StringTbl).all())
        print list(self.t.select().execute())
        s.refresh(f)
        print "After refresh, f = '%s'"%(f)

    def runTest(self):
        self.setUp()
        #self.testInsert()
        self.testObjCreate()
        #testDelAqStr()
        self.tearDown()

if __name__ == "__main__":
    ta = testAqStr()
    ta.runTest()
