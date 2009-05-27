#!/ms/dist/python/PROJ/core/2.5.4/bin/python
""" tests network """
import __init__
import unittest

import aquilon.aqdb.depends

from aquilon.aqdb.model import Network
from aquilon.aqdb.db_factory  import db_factory

#class testNetwork(unittest.TestCase):
class testNet():
    def setUp(self, *args, **kw):
        self.db = db_factory()
        self.s = self.db.Session()
        self.a = self.s.query(Network).first()

    def tearDown(self, *args, **kw):
        pass

    def testLocation(self):
        assert(self.a.location)

    def testAddresses(self):
        assert(self.a.addresses())

    def testNetmask(self):
        assert(self.a.netmask())

    def testGateway(self):
        assert(self.a.first_host())

    def testBroadcast(self):
        assert(self.a.last_host())

    def testCidr(self):
        assert(self.a.cidr)

    def testIp(self):
        assert(self.a.ip)

    def testName(self):
        assert(self.a.name)

    def testSide(self):
        assert(self.a.side)

    def testNetType(self):
        assert(self.a.network_type)

    def runTest(self):
        self.setUp()
        self.testLocation()
        self.testNetmask()
        self.testGateway()
        self.testBroadcast()
        self.tearDown()

if __name__ == "__main__":
    import nose
    nose.runmodule()

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon
