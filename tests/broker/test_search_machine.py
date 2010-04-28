#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010  Contributor
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
"""Module for testing the search machine command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.6"))

from brokertest import TestBrokerCommand


class TestSearchMachine(TestBrokerCommand):

    def testclusteravailable(self):
        command = "search machine --cluster utecl1"
        out = self.commandtest(command.split(" "))
        for i in range(1, 9):
            self.matchoutput(out, "evm%s" % i, command)
        self.matchclean(out, "evm9", command)

    def testclusterunavailable(self):
        command = "search machine --cluster cluster-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Cluster cluster-does-not-exist not found.",
                         command)

    def testlocation(self):
        # Should only show virtual machines, since all the physical machines
        # are at the rack level and this search is exact.
        command = "search machine --building ut"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "evm", command)
        self.matchclean(out, "ut", command)

    def testfailcpucount(self):
        command = "search machine --cpucount BAD"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Expected an integer for cpucount", command)

    def testcpucount(self):
        command = "search machine --cpucount 1"
        out = self.commandtest(command.split(" "))
        # Currently only virtual machines have 1 cpu in the tests...
        for i in range(1, 10):
            self.matchoutput(out, "evm%s" % i, command)
        self.matchclean(out, "ut", command)

    def testmemory(self):
        command = "search machine --memory 8192"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ut3c5n10", command)
        self.matchoutput(out, "evm1", command)
        # Has a different memory amount...
        self.matchclean(out, "ut9s03p1", command)

    def testfullinfo(self):
        command = "search machine --machine evm1 --fullinfo"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Virtual_machine: evm1", command)
        self.matchoutput(out, "Hosted by esx cluster: utecl1", command)
        self.matchoutput(out, "Vendor: utvendor Model: utmedium", command)

    def testexactcpu(self):
        command = ["search_machine", "--cpuname=xeon_2500", "--cpuspeed=2500",
                   "--cpuvendor=intel"]
        out = self.commandtest(command)
        self.matchoutput(out, "ut9s03p1", command)
        self.matchoutput(out, "evm1", command)
        # Has a different cpu...
        self.matchclean(out, "ut3c5n10", command)

    def testexactcpufailvendor(self):
        command = ["search_machine", "--cpuname=xeon_2500", "--cpuspeed=2500",
                   "--cpuvendor=vendor-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Vendor vendor-does-not-exist not found.",
                         command)

    def testfailexactcpu(self):
        command = ["search_machine", "--cpuname=xeon_2500", "--cpuspeed=0",
                   "--cpuvendor=intel"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "CPU vendor='intel' name='xeon_2500' speed='0' "
                         "not found.",
                         command)

    def testparialcpufailvendor(self):
        command = ["search_machine", "--cpuvendor=vendor-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Vendor vendor-does-not-exist not found.",
                         command)

    def testpartialcpu(self):
        command = ["search_machine", "--cpuspeed=2500", "--cpuvendor=intel"]
        out = self.commandtest(command)
        self.matchoutput(out, "ut9s03p1", command)
        self.matchoutput(out, "evm1", command)
        # Has a different cpu...
        self.matchclean(out, "ut3c5n10", command)

    def testcpuname(self):
        command = ["search_machine", "--cpuname=xeon_2500"]
        out = self.commandtest(command)
        self.matchoutput(out, "ut9s03p1", command)
        self.matchoutput(out, "evm1", command)
        # Has a different cpu...
        self.matchclean(out, "ut3c5n10", command)

    def testshare(self):
        command = ["search_machine", "--share=test_share_1"]
        out = self.commandtest(command)
        self.matchoutput(out, "evm1", command)
        self.matchclean(out, "evm2", command)
        self.matchclean(out, "evm10", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSearchMachine)
    unittest.TextTestRunner(verbosity=2).run(suite)

