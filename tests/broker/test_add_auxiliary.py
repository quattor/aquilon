#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Module for testing the add auxiliary command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestAddAuxiliary(TestBrokerCommand):

    def testaddunittest00e1(self):
        ip = self.net["unknown0"].usable[3]
        self.dsdb_expect_add("unittest00-e1.one-nyp.ms.com", ip, "eth1", ip.mac,
                             "unittest00.one-nyp.ms.com")
        self.noouttest(["add", "auxiliary", "--ip", ip,
                        "--auxiliary", "unittest00-e1.one-nyp.ms.com",
                        "--machine", "ut3c1n3", "--interface", "eth1"])
        self.dsdb_verify()

    def testverifyaddunittest00e1(self):
        command = "show auxiliary --auxiliary unittest00-e1.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Auxiliary: unittest00-e1.one-nyp.ms.com [%s]" %
                         self.net["unknown0"].usable[3],
                         command)
        self.searchoutput(out,
                          r"Interface: eth1 %s$" %
                          self.net["unknown0"].usable[3].mac,
                          command)
        self.matchoutput(out, "Machine: ut3c1n3", command)
        self.matchoutput(out, "Model Type: blade", command)

    def testverifyauxiliaryall(self):
        command = ["show", "auxiliary", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "unittest00-e1.one-nyp.ms.com", command)

    def testrejectmultipleaddress(self):
        command = ["add", "auxiliary", "--ip", self.net["unknown0"].usable[-1],
                   "--auxiliary", "unittest00-e2.one-nyp.ms.com",
                   "--hostname", "unittest00.one-nyp.ms.com",
                   "--interface", "eth1"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Interface eth1 of machine unittest00.one-nyp.ms.com "
                         "already has the following addresses: "
                         "eth1 [%s]" % self.net["unknown0"].usable[3],
                         command)

    # TODO: can't check this with the aq client since it detects the conflict
    # itself. Move this check to test_client_bypass once that can use knc
    #def testhostmachinemismatch(self):
    #    command = ["add", "auxiliary", "--ip", self.net["unknown0"].usable[-1],
    #               "--auxiliary", "unittest00-e2.one-nyp.ms.com",
    #               "--hostname", "unittest00.one-nyp.ms.com",
    #               "--machine", "ut3c1n5", "--interface", "eth1"]
    #    out = self.badrequesttest(command)
    #    self.matchoutput(out, "Use either --hostname or --machine to uniquely",
    #                     command)

    def testrejectut3c1n4eth1(self):
        # This is an IP address outside of the Firm.  It should not appear
        # in the network table and thus should trigger a bad request here.
        command = ["add", "auxiliary",
                   "--auxiliary", "unittest01-e1.one-nyp.ms.com",
                   "--machine", "ut3c1n4", "--mac", "02:02:c7:62:10:04",
                   "--interface", "eth1", "--ip", "199.98.16.4"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Could not determine network", command)

    def testverifyrejectut3c1n4eth1(self):
        command = "show machine --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Interface: eth1", command)

    def testrejectsixthip(self):
        # This tests that the sixth ip offset on a tor_switch network
        # gets rejected.
        command = ["add", "auxiliary",
                   "--auxiliary", "unittest01-e1.one-nyp.ms.com",
                   "--machine", "ut3c1n4", "--interface", "eth2",
                   "--mac", self.net["tor_net_0"].reserved[0].mac,
                   "--ip", self.net["tor_net_0"].reserved[0]]
        out = self.badrequesttest(command)
        self.matchoutput(out, "reserved for dynamic DHCP", command)

    def testverifyrejectsixthip(self):
        command = "show machine --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Interface: eth2", command)

    def testrejectseventhip(self):
        # This tests that the seventh ip offset on a tor_switch network
        # gets rejected.
        command = ["add", "auxiliary",
                   "--auxiliary", "unittest01-e1.one-nyp.ms.com",
                   "--machine", "ut3c1n4", "--interface", "eth3",
                   "--mac", self.net["tor_net_0"].reserved[1].mac,
                   "--ip", self.net["tor_net_0"].reserved[1]]
        out = self.badrequesttest(command)
        self.matchoutput(out, "reserved for dynamic DHCP", command)

    def testverifyrejectseventhip(self):
        command = "show machine --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Interface: eth3", command)

    def testrejectmacinuse(self):
        command = ["add", "auxiliary",
                   "--auxiliary", "unittest01-e4.one-nyp.ms.com",
                   "--machine", "ut3c1n4", "--interface", "eth4",
                   "--mac", self.net["tor_net_0"].usable[0].mac,
                   "--ip", self.net["tor_net_0"].usable[0]]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "MAC address %s is already in use" %
                         self.net["tor_net_0"].usable[0].mac,
                         command)

    def testverifyrejectmacinuse(self):
        command = "show machine --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Interface: eth4", command)

    def testautoipbadiface(self):
        # There is no e4 interface so it will be auto-created
        command = ["add", "auxiliary", "--autoip",
                   "--auxiliary", "unittest01-e4.one-nyp.ms.com",
                   "--machine", "ut3c1n4", "--interface", "e4"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Interface e4 of machine unittest01.one-nyp.ms.com "
                         "has neither a MAC address nor port group information, "
                         "it is not possible to generate an IP address "
                         "automatically.",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddAuxiliary)
    unittest.TextTestRunner(verbosity=2).run(suite)
