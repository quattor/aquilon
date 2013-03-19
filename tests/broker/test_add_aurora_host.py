#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddAuroraHost(TestBrokerCommand):

    def testaddaurorawithnode(self):
        self.dsdb_expect("show_host -host_name %s" % self.aurora_with_node)
        self.dsdb_expect("show_rack -rack_name oy604")
        self.noouttest(["add", "aurora", "host",
                        "--osname", "linux", "--osversion", "5.0.1-x86_64",
                        "--hostname", self.aurora_with_node])
        self.dsdb_verify()

    def testverifyaddaurorawithnode(self):
        command = "show host --hostname %s.ms.com" % self.aurora_with_node
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Primary Name: %s" % self.aurora_with_node, command)
        self.matchoutput(out, "Aurora_node: %s" % self.aurora_with_node, command)
        self.matchoutput(out, "Chassis: oy604c2.ms.com", command)
        self.matchoutput(out, "Slot: 6", command)
        self.matchoutput(out, "Archetype: aurora", command)
        self.matchoutput(out, "Personality: generic", command)
        self.matchoutput(out, "Domain: ny-prod", command)
        self.matchoutput(out, "Status: ready", command)

        # Rack data from DSDB supported.
        self.matchoutput(out, "Row: b", command)
        self.matchoutput(out, "Column: 04", command)

    def testaddaurorawithoutnode(self):
        self.dsdb_expect("show_host -host_name %s" % self.aurora_without_node)
        self.noouttest(["add", "aurora", "host",
                        "--osname", "linux", "--osversion", "5.0.1-x86_64",
                        "--hostname", self.aurora_without_node])
        self.dsdb_verify()

    def testverifyaddaurorawithoutnode(self):
        command = "show host --hostname %s.ms.com" % self.aurora_without_node
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Primary Name: %s" % self.aurora_without_node,
                command)
        self.matchoutput(out, "Aurora_node: ", command)
        self.matchoutput(out, "Building: ", command)
        self.matchoutput(out, "Archetype: aurora", command)
        self.matchoutput(out, "Personality: generic", command)
        self.matchoutput(out, "Domain: ny-prod", command)
        self.matchoutput(out, "Status: ready", command)

    def testdsdbmissing(self):
        self.dsdb_expect("show_host -host_name not-in-dsdb", fail=True)
        command = ["add", "aurora", "host", "--hostname", "not-in-dsdb",
                   "--osname", "linux", "--osversion", "5.0.1-x86_64"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Could not find not-in-dsdb in DSDB", command)
        self.dsdb_verify()

    aurora_without_rack = "oy605c2n6"

    def testdsdbrackmissing(self):
        self.dsdb_expect("show_host -host_name %s" % self.aurora_without_rack)
        self.dsdb_expect("show_rack -rack_name oy605", fail=True)
        command = ["add", "aurora", "host",
                   "--hostname", self.aurora_without_rack,
                   "--osname", "linux", "--osversion", "5.0.1-x86_64"]
        out = self.statustest(command)
        self.matchoutput(out, "Rack oy605 not defined in DSDB.", command)
        self.dsdb_verify()

    def testverifydsdbrackmissing(self):
        command = "show host --hostname %s.ms.com" % self.aurora_with_node
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Building: oy", command)

    def testaddnyaqd1(self):
        self.dsdb_expect("show_host -host_name nyaqd1")
        self.noouttest(["add", "aurora", "host", "--hostname", "nyaqd1",
                        "--osname", "linux", "--osversion", "5.0.1-x86_64"])
        self.dsdb_verify()

    def testverifyaddnyaqd1(self):
        command = "show host --hostname nyaqd1.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Aurora_node: ny00l4as01", command)
        self.matchoutput(out, "Primary Name: nyaqd1.ms.com", command)

    def testshowmachine(self):
        command = "show machine --model aurora_model"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Aurora_node: ny00l4as01", command)

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


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddAuroraHost)
    unittest.TextTestRunner(verbosity=2).run(suite)
