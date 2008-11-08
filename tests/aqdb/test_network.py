#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
""" tests network """
import sys
import os
import unittest
#from exceptions import TypeError

DIR = os.path.dirname(os.path.realpath(__file__))
LIBDIR = os.path.join(DIR, "..", "..", "lib", "python2.5")
sys.path.insert(0, LIBDIR)
import aquilon.aqdb.depends

from aquilon.aqdb.net.network import Network
from aquilon.aqdb.db_factory  import db_factory

class testNetwork(unittest.TestCase):

    def setUp(self, *args, **kw):
        self.db = db_factory()
        self.a = self.db.s.query(Network).first()

    def tearDown(self, *args, **kw):
        pass

    def testLocation(self):
        self.assert_(self.a.location)

    def testAddresses(self):
        self.assert_(self.a.addresses())

    def testNetmask(self):
        self.assert_(self.a.netmask())

    def testGateway(self):
        self.assert_(self.a.first_host())

    def testBroadcast(self):
        self.assert_(self.a.last_host())

    def testCidr(self):
        self.assert_(self.a.cidr)

    def testIp(self):
        self.assert_(self.a.ip)

    def testName(self):
        self.assert_(self.a.name)

    def testSide(self):
        self.assert_(self.a.side)

    def testNetType(self):
        self.assert_(self.a.network_type)

    def runTest(self):
        self.setUp()
        self.testLocation()
        self.testNetmask()
        self.testGateway()
        self.testBroadcast()
        self.tearDown()

if __name__ == "__main__":
    tnet = testNetwork()
    tnet.runTest()

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon
