#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
""" run load_all() from shutils and see to it that everything compiles as
    a first pass to get us some code coverage """

import sys
import os
import unittest

DIR = os.path.dirname(os.path.realpath(__file__))
LIBDIR = os.path.join(DIR, "..", "..", "lib", "python2.5")
sys.path.insert(0, LIBDIR)
import aquilon.aqdb.depends

class testCompile(unittest.TestCase):

    def setUp(self, *args, **kw):
        #TODO: recursively rm -fr *.pyc
        pass

    def tearDown(self, *args, **kw):
        #TODO: also recursively rm -fr *.pyc
        pass

    def testIncludes(self, *args, **kw):
        import sqlalchemy
        assert sqlalchemy.__version__

    def testLoadAll(self, *args, **kw):
        from aquilon.aqdb.utils.shutils import load_all
        load_all(verbose=1)

    def testSimpleQueryNetwork(self):
        from   aquilon.aqdb.net.network   import Network
        from   aquilon.aqdb.db_factory    import db_factory

        self.db = db_factory()
        self.a = self.db.s.query(Network).first()
        self.assert_(self.a.netmask())

    def runTest(self):
        self.setUp()
        self.testIncludes()
        self.testLoadAll()
        self.testSimpleQueryNetwork()
        self.tearDown()

if __name__ == "__main__":
    c = testCompile()
    c.runTest()

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon
