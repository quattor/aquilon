#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013  Contributor
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
"""Module for testing the add switch command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand
from switchtest import VerifySwitchMixin


class TestAddSwitch(TestBrokerCommand, VerifySwitchMixin):

    def testaddut3gd1r01(self):
        ip = self.net.tor_net[12].usable[0]
        self.dsdb_expect_add("ut3gd1r01.aqd-unittest.ms.com", ip, "xge")
        self.successtest(["add", "switch", "--type", "bor",
                          "--switch", "ut3gd1r01.aqd-unittest.ms.com",
                          "--ip", ip, "--rack", "ut3",
                          "--model", "uttorswitch", "--serial", "SNgd1r01"])
        self.dsdb_verify()

    def testaddut3gd1r04(self):
        ip = self.net.tor_net[6].usable[0]
        self.dsdb_expect_add("ut3gd1r04.aqd-unittest.ms.com", ip, "xge49",
                             ip.mac, comments="Some switch comments")
        self.successtest(["add", "switch", "--type", "tor",
                          "--switch", "ut3gd1r04.aqd-unittest.ms.com",
                          "--ip", ip, "--mac", ip.mac, "--interface", "xge49",
                          "--rack", "ut3", "--model", "temp_switch",
                          "--comments", "Some switch comments"])
        self.dsdb_verify()

    def testaddut3gd1r05(self):
        ip = self.net.tor_net[7].usable[0]
        self.dsdb_expect_add("ut3gd1r05.aqd-unittest.ms.com", ip, "xge49")
        self.successtest(["add", "switch", "--type", "tor",
                          "--switch", "ut3gd1r05.aqd-unittest.ms.com",
                          "--ip", ip, "--interface", "xge49",
                          "--rack", "ut3", "--model", "temp_switch",
                          "--vendor", "generic"])
        self.dsdb_verify()

    def testaddut3gd1r06(self):
        ip = self.net.tor_net[8].usable[0]
        self.dsdb_expect_add("ut3gd1r06.aqd-unittest.ms.com", ip, "xge")
        self.successtest(["add", "switch", "--type", "tor",
                          "--switch", "ut3gd1r06.aqd-unittest.ms.com",
                          "--ip", ip, "--rack", "ut3", "--model", "temp_switch",
                          "--vendor", "generic"])
        self.dsdb_verify()

    def testaddut3gd1r07(self):
        ip = self.net.tor_net[9].usable[0]
        self.dsdb_expect_add("ut3gd1r07.aqd-unittest.ms.com", ip, "xge")
        self.successtest(["add", "switch", "--type", "bor",
                          "--switch", "ut3gd1r07.aqd-unittest.ms.com",
                          "--ip", ip, "--rack", "ut3", "--model", "temp_switch"])
        self.dsdb_verify()

    def testrejectut3gd1r99(self):
        command = ["add", "switch", "--switch", "ut3gd1r99.aqd-unittest.ms.com",
                   "--type", "bor", "--ip", self.net.tor_net[9].usable[0],
                   "--rack", "ut3", "--model", "temp_switch"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "IP address %s is already in use" %
                         self.net.tor_net[9].usable[0],
                         command)

    def testverifyaddut3gd1r01(self):
        self.verifyswitch("ut3gd1r01.aqd-unittest.ms.com", "hp", "uttorswitch",
                          "ut3", "a", "3", "SNgd1r01", switch_type='bor',
                          ip=self.net.tor_net[12].usable[0])

        command = ["show", "switch", "--switch",
                   "ut3gd1r01.aqd-unittest.ms.com", "--format", "csv"]
        out = self.commandtest(command)
        self.matchoutput(out, "ut3gd1r01.aqd-unittest.ms.com,4.2.5.8,bor,"
                         "ut3,ut,hp,uttorswitch,SNgd1r01,,", command)

    def testverifyaddut3gd1r04(self):
        self.verifyswitch("ut3gd1r04.aqd-unittest.ms.com", "generic",
                          "temp_switch", "ut3", "a", "3", switch_type='tor',
                          ip=self.net.tor_net[6].usable[0],
                          mac=self.net.tor_net[6].usable[0].mac,
                          interface="xge49",
                          comments="Some switch comments")

    def testverifyaddut3gd1r05(self):
        self.verifyswitch("ut3gd1r05.aqd-unittest.ms.com", "generic",
                          "temp_switch", "ut3", "a", "3", switch_type='tor',
                          ip=self.net.tor_net[7].usable[0],
                          interface="xge49")

    def testverifyaddut3gd1r06(self):
        self.verifyswitch("ut3gd1r06.aqd-unittest.ms.com", "generic",
                          "temp_switch", "ut3", "a", "3", switch_type='tor',
                          ip=self.net.tor_net[8].usable[0])

    def testverifyaddut3gd1r07(self):
        self.verifyswitch("ut3gd1r07.aqd-unittest.ms.com", "generic",
                          "temp_switch", "ut3", "a", "3", switch_type='bor',
                          ip=self.net.tor_net[9].usable[0])

    def testrejectbadlabelimplicit(self):
        command = ["add", "switch", "--switch", "not-alnum.aqd-unittest.ms.com",
                   "--type", "bor", "--ip", self.net.tor_net[9].usable[-1],
                   "--rack", "ut3", "--model", "temp_switch"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Could not deduce a valid hardware label",
                         command)

    def testrejectbadlabelexplicit(self):
        command = ["add", "switch", "--switch", "ut3gd1r99.aqd-unittest.ms.com",
                   "--label", "not-alnum",
                   "--type", "bor", "--ip", self.net.tor_net[9].usable[-1],
                   "--rack", "ut3", "--model", "temp_switch"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Illegal hardware label format 'not-alnum'.",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddSwitch)
    unittest.TextTestRunner(verbosity=2).run(suite)
