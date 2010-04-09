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
"""Module for testing the add manager command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.6"))

from brokertest import TestBrokerCommand


class TestAddManager(TestBrokerCommand):

    # Note: If changing this, also change testverifyshowmissingmanager
    # in test_add_aquilon_host.py.
    def testaddunittest00r(self):
        self.noouttest(["add", "manager",
                        "--ip", self.net.unknown[0].usable[4].ip,
                        "--hostname", "unittest00.one-nyp.ms.com"])

    def testverifyaddunittest00r(self):
        command = "show manager --manager unittest00r.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Manager: unittest00r.one-nyp.ms.com", command)
        self.matchoutput(out, "IP: %s" % self.net.unknown[0].usable[4].ip,
                         command)
        self.matchoutput(out, "MAC: %s" % self.net.unknown[0].usable[4].mac,
                         command)
        self.matchoutput(out,
                         "Interface: bmc %s boot=False" %
                         self.net.unknown[0].usable[4].mac,
                         command)
        self.matchoutput(out, "Blade: ut3c1n3", command)

    def testverifyunittest00(self):
        command = "show host --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Manager: unittest00r.one-nyp.ms.com [%s]" %
                         self.net.unknown[0].usable[4].ip,
                         command)

    def testverifycatut3c1n3interfaces(self):
        command = "cat --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, """"console/bmc" = nlist(""", command)
        self.matchoutput(out,
                         '"hwaddr", "%s"' %
                         self.net.unknown[0].usable[4].mac.lower(),
                         command)
        self.matchoutput(out, '"fqdn", "%s"' % "unittest00r.one-nyp.ms.com",
                         command)

    def testaddunittest02rsa(self):
        self.noouttest(["add", "manager", "--interface", "ilo",
                        "--ip", self.net.unknown[0].usable[9].ip,
                        "--hostname", "unittest02.one-nyp.ms.com",
                        "--manager", "unittest02rsa.one-nyp.ms.com",
                        "--mac", self.net.unknown[0].usable[9].mac])

    def testverifyaddunittest02rsa(self):
        command = "show manager --manager unittest02rsa.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Manager: unittest02rsa.one-nyp.ms.com", command)
        self.matchoutput(out, "IP: %s" % self.net.unknown[0].usable[9].ip,
                         command)
        self.matchoutput(out, "MAC: %s" % self.net.unknown[0].usable[9].mac,
                         command)
        self.matchoutput(out,
                         "Interface: ilo %s boot=False" %
                         self.net.unknown[0].usable[9].mac,
                         command)
        self.matchoutput(out, "Blade: ut3c5n10", command)

    def testverifyunittest02(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Manager: unittest02rsa.one-nyp.ms.com [%s]" %
                         self.net.unknown[0].usable[9].ip,
                         command)

    def testaddbadunittest12bmc(self):
        command = ["add", "interface", "--interface", "bmc",
                   "--hostname", "unittest12.aqd-unittest.ms.com",
                   "--mac", self.net.unknown[0].usable[7].mac]
        out = self.badrequesttest(command)
        self.matchoutput(out, "already has an interface with mac", command)

    def testfailaddunittest12bmc(self):
        command = ["add", "manager", "--ip", self.net.unknown[0].usable[0].ip,
                   "--hostname", "unittest02.one-nyp.ms.com",
                   "--manager", "unittest02ipmi.one-nyp.ms.com",
                   "--interface", "ipmi",
                   "--mac", self.net.unknown[0].usable[0].mac]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Mac '%s' already in use" %
                         self.net.unknown[0].usable[0].mac,
                         command)

    # Taking advantage of the fact that this runs after add_machine
    # and add_host, and that this *should* create a manager
    # Lots of verifications steps for this single test...
    def testaddunittest12bmc(self):
        command = ["add", "interface", "--interface", "bmc",
                   "--hostname", "unittest12.aqd-unittest.ms.com",
                   "--mac", self.net.unknown[0].usable[8].mac]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "Renaming machine 'ut3s01p1a' as 'ut3s01p1'",
                         command)

    # Test that the interface cannot be removed as long as the manager exists
    def testdelinterface(self):
        command = ["del", "interface", "--mac",
                   self.net.unknown[0].usable[8].mac]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "manager unittest12r.aqd-unittest.ms.com still exists",
                         command)

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
        self.matchoutput(out, "IP: %s" % self.net.unknown[0].usable[7].ip,
                         command)
        self.matchoutput(out, "Hostname: unittest12.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out,
                         "Manager: unittest12r.aqd-unittest.ms.com [%s]" %
                         self.net.unknown[0].usable[8].ip,
                         command)
        self.matchoutput(out, "Interface: eth0 %s boot=True" %
                         self.net.unknown[0].usable[7].mac.lower(), command)
        self.matchoutput(out, "Interface: bmc %s boot=False" %
                         self.net.unknown[0].usable[8].mac.lower(), command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddManager)
    unittest.TextTestRunner(verbosity=2).run(suite)

