#!/usr/bin/env python2.5
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008  Contributor
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

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestAddAuxiliary(TestBrokerCommand):

    def testaddunittest00e1(self):
        self.noouttest(["add", "auxiliary", "--ip", self.hostip3,
            "--auxiliary", "unittest00-e1.one-nyp.ms.com",
            "--machine", "ut3c1n3", "--interface", "eth1"])

    def testverifyaddunittest00e1(self):
        command = "show auxiliary --auxiliary unittest00-e1.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Auxiliary: unittest00-e1.one-nyp.ms.com", command)
        self.matchoutput(out, "IP: %s" % self.hostip3, command)
        self.matchoutput(out, "MAC: %s" % self.hostmac3, command)
        self.matchoutput(out, "Interface: eth1 %s boot=False" % self.hostmac3,
                         command)
        self.matchoutput(out, "Blade: ut3c1n3", command)

    def testrejectut3c1n4eth1(self):
        # This is an old (relatively) well known DNS server sitting out
        # on the net that will probably never be controlled by the Firm.
        # It should not appear in our network table, and thus should
        # trigger a bad request here.
        command = ["add", "auxiliary",
            "--auxiliary", "unittest01-e1.one-nyp.ms.com",
            "--machine", "ut3c1n4", "--mac", "02:02:04:02:02:04",
            "--interface", "eth1", "--ip", "4.2.2.4"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Could not determine network", command)

    def testverifyrejectut3c1n4eth1(self):
        command = "show machine --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Interface: eth1", command)

    def testrejectsixthip(self):
        # This tests that the sixth ip offset on a tor_switch network
        # gets rejected.
        # FIXME: Hard-coded.  Assumes the 8.8.4.0 subnet, since all
        # the tests are using 8.8.[4567].* ips.
        command = ["add", "auxiliary",
            "--auxiliary", "unittest01-e1.one-nyp.ms.com",
            "--machine", "ut3c1n4", "--mac", "02:02:08:08:04:06",
            "--interface", "eth2", "--ip", "8.8.4.6"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "reserved for dynamic dhcp", command)

    def testverifyrejectsixthip(self):
        command = "show machine --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Interface: eth2", command)

    def testrejectseventhip(self):
        # This tests that the seventh ip offset on a tor_switch network
        # gets rejected.
        # FIXME: Hard-coded.  Assumes the 8.8.4.0 subnet, since all
        # the tests are using 8.8.[4567].* ips.
        command = ["add", "auxiliary",
            "--auxiliary", "unittest01-e1.one-nyp.ms.com",
            "--machine", "ut3c1n4", "--mac", "02:02:08:08:04:07",
            "--interface", "eth3", "--ip", "8.8.4.7"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "reserved for dynamic dhcp", command)

    def testverifyrejectseventhip(self):
        command = "show machine --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Interface: eth3", command)

    def testrejectmacinuse(self):
        command = ["add", "auxiliary",
            "--auxiliary", "unittest01-e4.one-nyp.ms.com",
            "--machine", "ut3c1n4", "--mac", self.hostmac4,
            "--interface", "eth4", "--ip", "8.8.4.7"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Mac '%s' already in use" % self.hostmac4,
                         command)

    def testverifyrejectseventhip(self):
        command = "show machine --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Interface: eth4", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddAuxiliary)
    unittest.TextTestRunner(verbosity=2).run(suite)

