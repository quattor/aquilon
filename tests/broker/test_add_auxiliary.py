#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
"""Module for testing the add auxiliary command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddAuxiliary(TestBrokerCommand):

    def testaddunittest00e1(self):
        ip = self.net.unknown[0].usable[3]
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
                         self.net.unknown[0].usable[3],
                         command)
        self.matchoutput(out,
                         "Interface: eth1 %s boot=False" %
                         self.net.unknown[0].usable[3].mac,
                         command)
        self.matchoutput(out, "Blade: ut3c1n3", command)

    def testverifyauxiliaryall(self):
        command = ["show", "auxiliary", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "unittest00-e1.one-nyp.ms.com", command)

    def testrejectmultipleaddress(self):
        command = ["add", "auxiliary", "--ip", self.net.unknown[0].usable[-1],
                   "--auxiliary", "unittest00-e2.one-nyp.ms.com",
                   "--hostname", "unittest00.one-nyp.ms.com",
                   "--interface", "eth1"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Interface eth1 of machine unittest00.one-nyp.ms.com "
                         "already has the following addresses: "
                         "eth1 [%s]" % self.net.unknown[0].usable[3],
                         command)

    # TODO: can't check this with the aq client since it detects the conflict
    # itself. Move this check to test_client_bypass once that can use knc
    #def testhostmachinemismatch(self):
    #    command = ["add", "auxiliary", "--ip", self.net.unknown[0].usable[-1],
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
                   "--mac", self.net.tor_net[0].reserved[0].mac,
                   "--ip", self.net.tor_net[0].reserved[0]]
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
                   "--mac", self.net.tor_net[0].reserved[1].mac,
                   "--ip", self.net.tor_net[0].reserved[1]]
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
                   "--mac", self.net.tor_net[0].usable[0].mac,
                   "--ip", self.net.tor_net[0].usable[0]]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "MAC address %s is already in use" %
                         self.net.tor_net[0].usable[0].mac,
                         command)

    def testverifyrejectseventhip(self):
        command = "show machine --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Interface: eth4", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddAuxiliary)
    unittest.TextTestRunner(verbosity=2).run(suite)

