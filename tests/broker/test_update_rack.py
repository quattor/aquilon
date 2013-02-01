#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012  Contributor
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
"""Module for testing the update rack command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUpdateRack(TestBrokerCommand):
    # Was row a column 3
    def testupdateut3(self):
        self.noouttest(["update", "rack", "--rack", "ut3", "--row", "b"])

    # Was row g column 2
    def testupdateut8(self):
        self.noouttest(["update", "rack", "--rack", "ut8", "--column", "8"])

    # Was row g column 3
    def testupdateut9(self):
        self.noouttest(["update", "rack", "--rack", "ut9", "--row", "h",
                        "--column", "9", "--fullname", "My Rack",
                        "--comments", "Testing a rack update"])

    def testverifyupdateut9(self):
        command = "show rack --rack ut9"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Rack: ut9", command)
        self.matchoutput(out, "Fullname: My Rack", command)
        self.matchoutput(out, "Row: h", command)
        self.matchoutput(out, "Column: 9", command)
        self.matchoutput(out, "Comments: Testing a rack update", command)

    # Was row zz column 99
    def testupdatenp997(self):
        self.noouttest(["update", "rack", "--rack", "np997", "--row", "xx",
                        "--column", "77", "--fullname", "My Other Rack",
                        "--comments", "Testing another rack update"])

    def testverifyupdatenp997(self):
        command = "show rack --rack np997"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Rack: np997", command)
        self.matchoutput(out, "Fullname: My Other Rack", command)
        self.matchoutput(out, "Row: xx", command)
        self.matchoutput(out, "Column: 77", command)
        self.matchoutput(out, "Comments: Testing another rack update", command)

    # Was row yy column 88
    def testupdatenp998(self):
        self.noouttest(["update", "rack", "--rack", "np998", "--row", "vv",
                        "--column", "66"])

    def testfailrow(self):
        command = ["update", "rack", "--rack", "np999", "--row", "a-b"]
        err = self.badrequesttest(command)
        self.matchoutput(err, "must be alphanumeric", command)

    def testalphacolumn(self):
        """ we now accept characters for rack columns   """
        command = ["update", "rack", "--rack", "np999", "--column", "a"]
        err = self.noouttest(command)

    def testverifyshowallcsv(self):
        command = "show rack --all --format=csv"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "rack,ut3,room,utroom1,b,3", command)
        self.matchoutput(out, "rack,ut8,building,ut,g,8", command)
        self.matchoutput(out, "rack,ut9,room,utroom2,h,9", command)
        self.matchoutput(out, "rack,np997,building,np,xx,77", command)
        self.matchoutput(out, "rack,np998,building,np,vv,66", command)
        self.matchoutput(out, "rack,np999,building,np,zz,a", command)

    def testverifyut3plenary(self):
        command = "cat --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"rack/name" = "ut3";', command)
        self.matchoutput(out, '"rack/row" = "b";', command)
        self.matchoutput(out, '"rack/column" = "3";', command)

    def testverifyut8plenary(self):
        command = "cat --machine ut8s02p1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"rack/name" = "ut8";', command)
        self.matchoutput(out, '"rack/row" = "g";', command)
        self.matchoutput(out, '"rack/column" = "8";', command)

    def testverifyut9plenary(self):
        command = "cat --machine ut9s03p1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"rack/name" = "ut9";', command)
        self.matchoutput(out, '"rack/row" = "h";', command)
        self.matchoutput(out, '"rack/column" = "9";', command)

    def test_100_updateroom(self):
        command = ['update_rack', '--rack=ut8', '--room=utroom1']
        self.noouttest(command)

    def test_110_verifyroom(self):
        command = ['show_rack', '--rack=ut8']
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'Location Parents: \[.*Building ut, Room utroom1\]',
                          command)

    def test_120_swaproom(self):
        command = ['update_rack', '--rack=ut8', '--room=utroom2']
        self.noouttest(command)

    def test_130_verifyroom(self):
        command = ['show_rack', '--rack=ut8']
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'Location Parents: \[.*Building ut, Room utroom2\]',
                          command)

    def test_140_clearroom(self):
        command = ['update_rack', '--rack=ut8', '--clearroom']
        self.noouttest(command)

    def test_150_verifyclear(self):
        command = ['show_rack', '--rack=ut8']
        out = self.commandtest(command)
        self.searchclean(out, r'Location Parents: \[.* Room .*\]', command)

    def test_160_failcleartwice(self):
        command = ['update_rack', '--rack=ut8', '--clearroom']
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         'Rack ut8 does not have room information to clear.',
                         command)

    def test_170_failchangebuilding(self):
        command = ['update_rack', '--rack=ut8', '--room=np-lab1']
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Cannot change buildings.  Room np-lab1 is in "
                         "Building np while Rack ut8 is in Building ut.",
                         command)

    def test_200_defaultdns(self):
        command = ["update", "rack", "--rack", "ut9",
                   "--default_dns_domain", "aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_210_verify_defaultdns(self):
        command = ["show", "rack", "--rack", "ut9"]
        out = self.commandtest(command)
        self.matchoutput(out, "Default DNS Domain: aqd-unittest.ms.com",
                         command)

    def test_220_clear_defaultdns(self):
        command = ["update", "rack", "--rack", "ut9",
                   "--default_dns_domain", ""]
        self.noouttest(command)

    def test_230_verify_defaultdns_gone(self):
        command = ["show", "rack", "--rack", "ut9"]
        out = self.commandtest(command)
        self.matchclean(out, "Default DNS", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateRack)
    unittest.TextTestRunner(verbosity=2).run(suite)
