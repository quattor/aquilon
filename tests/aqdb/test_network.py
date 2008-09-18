#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
""" tests network """
import sys
import os
import msversion
import unittest
from exceptions import TypeError

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..", "lib", "python2.5")
    sys.path.insert(0, SRCDIR)
    #import nose

import aquilon.aqdb.depends
import aquilon.aqdb.net
from   aquilon.aqdb.db_factory    import db_factory
from   aquilon.aqdb.net.network   import Network
from   aquilon.aqdb.utils.shutils import load_all

class testNetwork(unittest.TestCase):

    def setUp(self, *args, **kw):
        #load_all()
        self.db = db_factory()
        n = aquilon.aqdb.net.network.Network
        self.a = self.db.s.query(n).first()

    def tearDown(self, *args, **kw):
        pass

    def testNetmask(self):
        self.assert_(self.a.netmask())
        print self.a.netmask()

    def testGateway(self):
        self.assert_(self.a.first_host())
        print self.a.first_host()

    def testBroadcast(self):
        self.assert_(self.a.last_host())
        print self.a.last_host()

    def runTest(self):
        self.setUp()
        self.testNetmask()
        self.testGateway()
        self.testBroadcast()
        self.tearDown()

if __name__ == "__main__":
    tnet = testNetwork()
    tnet.runTest()

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon
