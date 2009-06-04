#!/usr/bin/env python2.5
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
""" tests the AqStr column_type """
import sys
import os

import unittest

if __name__ == "__main__":
    #import testing_depends
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..", "lib", "python2.5")
    sys.path.insert(0, SRCDIR)
#import nose

import aquilon.aqdb.depends

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


