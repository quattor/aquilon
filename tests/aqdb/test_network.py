#!/usr/bin/env python2.5
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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

