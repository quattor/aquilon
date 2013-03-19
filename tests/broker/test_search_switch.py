#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2013  Contributor
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
"""Module for testing the search switch command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestSearchSwitch(TestBrokerCommand):

    def testwithinterfacecsv(self):
        command = ["search_switch", "--switch=ut3gd1r06.aqd-unittest.ms.com",
                   "--format=csv"]
        out = self.commandtest(command)
        ip = self.net.tor_net[8].usable[1]
        self.matchoutput(out,
                         "ut3gd1r06.aqd-unittest.ms.com,%s,tor,ut3,ut,"
                         "generic,temp_switch,,xge49,%s" % (ip, ip.mac),
                         command)

    def testwithoutinterfacecsv(self):
        command = ["search_switch", "--switch=ut3gd1r01.aqd-unittest.ms.com",
                   "--format=csv"]
        out = self.commandtest(command)
        ip = self.net.tor_net[12].usable[0]
        self.matchoutput(out,
                         "ut3gd1r01.aqd-unittest.ms.com,%s,bor,ut3,ut,"
                         "hp,uttorswitch,SNgd1r01,," % ip,
                         command)

    def testbuilding(self):
        command = ["search_switch", "--building=ut"]
        out = self.commandtest(command)
        self.matchoutput(out, "ut3gd1r05.aqd-unittest.ms.com", command)
        self.matchoutput(out, "ut3gd1r06.aqd-unittest.ms.com", command)
        self.matchclean(out, "Switch", command)

    def testbuildingexact(self):
        command = ["search_switch", "--building=ut", "--exact_location"]
        self.noouttest(command)

    def testrack(self):
        command = ["search_switch", "--rack=ut4"]
        out = self.commandtest(command)
        self.matchoutput(out, "ut3gd1r05.aqd-unittest.ms.com", command)
        self.matchclean(out, "ut3gd1r06.aqd-unittest.ms.com", command)

    def testmodel(self):
        command = ["search_switch", "--model=uttorswitch"]
        out = self.commandtest(command)
        self.matchoutput(out, "ut3gd1r04.aqd-unittest.ms.com", command)
        self.matchoutput(out, "ut3gd1r05.aqd-unittest.ms.com", command)
        self.matchclean(out, "ut3gd1r06.aqd-unittest.ms.com", command)

    def testvendor(self):
        command = ["search_switch", "--vendor=hp"]
        out = self.commandtest(command)
        self.matchoutput(out, "ut3gd1r04.aqd-unittest.ms.com", command)
        self.matchoutput(out, "ut3gd1r05.aqd-unittest.ms.com", command)
        self.matchclean(out, "ut3gd1r06.aqd-unittest.ms.com", command)

    def testtype(self):
        command = ["search_switch", "--type=bor"]
        out = self.commandtest(command)
        self.matchoutput(out, "ut3gd1r04.aqd-unittest.ms.com", command)
        self.matchclean(out, "ut3gd1r05.aqd-unittest.ms.com", command)
        self.matchclean(out, "ut3gd1r06.aqd-unittest.ms.com", command)

    def testserial(self):
        command = ["search_switch", "--serial=SNgd1r05_new"]
        out = self.commandtest(command)
        self.matchoutput(out, "ut3gd1r05.aqd-unittest.ms.com", command)
        self.matchclean(out, "ut3gd1r04.aqd-unittest.ms.com", command)

    def testserialandfullinfo(self):
        command = ["search_switch", "--serial=SNgd1r05_new", "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "Switch: ut3gd1r05", command)
        self.matchclean(out, "ut3gd1r04", command)

    def testfullinfocsv(self):
        command = ["search_switch", "--serial=SNgd1r05_new", "--fullinfo",
                   "--format=csv"]
        out = self.commandtest(command)
        ip = self.net.tor_net[7].usable[0]
        self.matchoutput(out,
                         "ut3gd1r05.aqd-unittest.ms.com,%s,tor,ut4,ut,"
                         "hp,uttorswitch,SNgd1r05_new,," % ip,
                         command)

    def testsearchswitchall(self):
        command = ["search_switch", "--all", "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "Switch: ut3gd1r01", command)
        self.matchoutput(out,
                         "Primary Name: ut3gd1r01.aqd-unittest.ms.com [%s]" %
                         self.net.tor_net[12].usable[0],
                         command)
        self.matchoutput(out, "Switch Type: bor", command)
        self.matchoutput(out, "Rack: ut3", command)
        self.matchoutput(out, "Vendor: hp Model: uttorswitch", command)
        self.matchoutput(out, "Serial: SNgd1r01", command)
        self.matchoutput(out, "Switch: ut3gd1r04", command)
        self.matchoutput(out,
                         "Primary Name: ut3gd1r04.aqd-unittest.ms.com [%s]" %
                         self.net.tor_net[6].usable[1],
                         command)
        self.matchoutput(out, "Switch Type: tor", command)

    def testsearchswitchswitch(self):
        command = ["search_switch", "--switch=ut3gd1r04.aqd-unittest.ms.com",
                   "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "Switch: ut3gd1r04", command)
        self.matchoutput(out,
                         "Primary Name: ut3gd1r04.aqd-unittest.ms.com [%s]" %
                         self.net.tor_net[6].usable[1],
                         command)
        self.matchoutput(out, "Switch Type: bor", command)
        self.matchoutput(out, "Rack: ut3", command)
        self.matchoutput(out, "Vendor: hp Model: uttorswitch", command)

    def testsearchswitchallcsv(self):
        command = ["search_switch", "--all", "--format=csv"]
        out = self.commandtest(command)
        ip = self.net.tor_net[8].usable[1]
        self.matchoutput(out,
                         "ut3gd1r06.aqd-unittest.ms.com,%s,tor,ut3,ut,"
                         "generic,temp_switch,,xge49,%s" % (ip, ip.mac),
                         command)
        ip = self.net.tor_net[12].usable[0]
        self.matchoutput(out,
                         "ut3gd1r01.aqd-unittest.ms.com,%s,bor,ut3,ut,"
                         "hp,uttorswitch,SNgd1r01,," % ip,
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSearchSwitch)
    unittest.TextTestRunner(verbosity=2).run(suite)
