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
"""Module for testing the add manager command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestAddManager(TestBrokerCommand):

    # Note: If changing this, also change testverifyshowmissingmanager
    # in test_add_aquilon_host.py.
    def testaddunittest00r(self):
        self.noouttest(["add", "manager", "--ip", self.hostip10,
            "--hostname", "unittest00.one-nyp.ms.com"])

    def testverifyaddunittest00r(self):
        command = "show manager --manager unittest00r.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Manager: unittest00r.one-nyp.ms.com", command)
        self.matchoutput(out, "IP: %s" % self.hostip10, command)
        self.matchoutput(out, "MAC: %s" % self.hostmac10, command)
        self.matchoutput(out, "Interface: bmc %s boot=False" % self.hostmac10,
                         command)
        self.matchoutput(out, "Blade: ut3c1n3", command)

    def testverifyunittest00(self):
        command = "show host --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Manager: unittest00r.one-nyp.ms.com [%s]" %
                         self.hostip10,
                         command)

    def testverifycatut3c1n3interfaces(self):
        command = "cat --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, """"console/bmc" = nlist(""", command)
        self.matchoutput(out, '"hwaddr", "%s"' % self.hostmac10.lower(),
                         command)
        self.matchoutput(out, '"fqdn", "%s"' % "unittest00r.one-nyp.ms.com",
                         command)

    def testaddunittest02rsa(self):
        self.noouttest(["add", "manager", "--ip", self.hostip11,
            "--hostname", "unittest02.one-nyp.ms.com",
            "--manager", "unittest02rsa.one-nyp.ms.com",
            "--interface", "ilo", "--mac", self.hostmac11])

    def testverifyaddunittest02rsa(self):
        command = "show manager --manager unittest02rsa.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Manager: unittest02rsa.one-nyp.ms.com", command)
        self.matchoutput(out, "IP: %s" % self.hostip11, command)
        self.matchoutput(out, "MAC: %s" % self.hostmac11, command)
        self.matchoutput(out, "Interface: ilo %s boot=False" % self.hostmac11,
                         command)
        self.matchoutput(out, "Blade: ut3c5n10", command)

    def testverifyunittest02(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Manager: unittest02rsa.one-nyp.ms.com [%s]" %
                         self.hostip11,
                         command)

    def testaddbadunittest12bmc(self):
        command = ["add", "interface", "--interface", "bmc",
                        "--hostname", "unittest12.aqd-unittest.ms.com",
                        "--mac", self.hostmac12]
        out = self.badrequesttest(command)
        self.matchoutput(out, "already has an interface with mac", command)

    def testfailaddunittest12bmc(self):
        command = ["add", "manager", "--ip", self.hostip10,
                   "--hostname", "unittest02.one-nyp.ms.com",
                   "--manager", "unittest02ipmi.one-nyp.ms.com",
                   "--interface", "ipmi", "--mac", self.hostmac10]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Mac '%s' already in use" % self.hostmac10,
                         command)

    # Taking advantage of the fact that this runs after add_machine
    # and add_host, and that this *should* create a manager
    # Lots of verifications steps for this single test...
    def testaddunittest12bmc(self):
        self.noouttest(["add", "interface", "--interface", "bmc",
                        "--hostname", "unittest12.aqd-unittest.ms.com",
                        "--mac", self.hostmac13])

    def testverifyunittest13removed(self):
        command = "show host --hostname unittest13.one-nyp.ms.com"
        self.notfoundtest(command.split(" "))

    def testverifyut3s01p1bremoved(self):
        command = "show machine --machine ut3s01p1b"
        self.notfoundtest(command.split(" "))

    def testverifyut3s01p1arenamed(self):
        command = "show machine --machine ut3s01p1a"
        self.notfoundtest(command.split(" "))
        command = "show machine --machine ut3s01p1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Rackmount: ut3s01p1", command)

    def testverifyunittest12(self):
        command = "show host --hostname unittest12.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "IP: %s" % self.hostip12, command)
        self.matchoutput(out, "Hostname: unittest12.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out,
                         "Manager: unittest12r.aqd-unittest.ms.com [%s]" %
                         self.hostip13,
                         command)
        self.matchoutput(out, "Interface: eth0 %s boot=True" %
                         self.hostmac12.lower(), command)
        self.matchoutput(out, "Interface: bmc %s boot=False" %
                         self.hostmac13.lower(), command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddManager)
    unittest.TextTestRunner(verbosity=2).run(suite)

