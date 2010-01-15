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
"""Module for testing the add aurora host command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestAddAuroraHost(TestBrokerCommand):

    def testaddaurorawithnode(self):
        self.noouttest(["add", "aurora", "host",
                        "--osname", "linux", "--osversion", "4.0.1-x86_64",
                        "--hostname", self.aurora_with_node])

    def testverifyaddaurorawithnode(self):
        command = "show host --hostname %s.ms.com" % self.aurora_with_node
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hostname: %s" % self.aurora_with_node, command)
        self.matchoutput(out, "Aurora_node: ", command)
        self.matchoutput(out, "Chassis: ", command)
        self.matchoutput(out, "Slot: ", command)
        self.matchoutput(out, "Archetype: aurora", command)
        self.matchoutput(out, "Personality: generic", command)
        self.matchoutput(out, "Domain: ny-prod", command)
        self.matchoutput(out, "Status: ready", command)

    def testaddaurorawithoutnode(self):
        self.noouttest(["add", "aurora", "host",
                        "--osname", "linux", "--osversion", "4.0.1-x86_64",
                        "--hostname", self.aurora_without_node])

    def testverifyaddaurorawithoutnode(self):
        command = "show host --hostname %s.ms.com" % self.aurora_without_node
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hostname: %s" % self.aurora_without_node,
                command)
        self.matchoutput(out, "Aurora_node: ", command)
        self.matchoutput(out, "Building: ", command)
        self.matchoutput(out, "Archetype: aurora", command)
        self.matchoutput(out, "Personality: generic", command)
        self.matchoutput(out, "Domain: ny-prod", command)
        self.matchoutput(out, "Status: ready", command)

    def testaddnyaqd1(self):
        self.noouttest(["add", "aurora", "host", "--hostname", "nyaqd1",
                        "--osname", "linux", "--osversion", "4.0.1-x86_64"])

    def testverifyaddnyaqd1(self):
        command = "show host --hostname nyaqd1.ms.com"
        out = self.commandtest(command.split(" "))

    def testcatmachine(self):
        command = "cat --machine %s" % self.aurora_without_node
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out,
                         "Plenary file not available for "
                         "aurora_node machines.",
                         command)

    def testshowhostproto(self):
        fqdn = self.aurora_with_node
        if not fqdn.endswith(".ms.com"):
            fqdn = "%s.ms.com" % fqdn
        command = ["show_host", "--hostname", fqdn, "--format=proto"]
        (out, err) = self.successtest(command)
        self.assertEmptyErr(err, command)
        hostlist = self.parse_hostlist_msg(out, expect=1)
        host = hostlist.hosts[0]
        self.assertEqual(host.fqdn, fqdn)
        self.assertEqual(host.ip, "")


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddAuroraHost)
    unittest.TextTestRunner(verbosity=2).run(suite)
