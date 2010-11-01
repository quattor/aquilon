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
"""Module for testing the del dynamic range command."""


import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from ipaddr import IPv4Address

from brokertest import TestBrokerCommand


class TestDelDynamicRange(TestBrokerCommand):

    def testdeldifferentnetworks(self):
        command = ["del_dynamic_range",
                   "--startip", self.net.tor_net2[0].usable[2],
                   "--endip", self.net.tor_net2[1].usable[2]]
        out = self.badrequesttest(command)
        self.matchoutput(out, "must be on the same subnet", command)

    # These rely on the ip never having been used...
    def testdelnothingfound(self):
        command = ["del_dynamic_range",
                   "--startip", self.net.tor_net2[0].usable[-2],
                   "--endip", self.net.tor_net2[0].usable[-1]]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Nothing found in range", command)

    def testdelnostart(self):
        command = ["del_dynamic_range",
                   "--startip", self.net.tor_net2[0].usable[1],
                   "--endip", self.net.tor_net2[0].usable[-3]]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "No system found with IP address %s" %
                         self.net.tor_net2[0].usable[1],
                         command)

    def testdelnoend(self):
        command = ["del_dynamic_range",
                   "--startip", self.net.tor_net2[0].usable[2],
                   "--endip", self.net.tor_net2[0].usable[-2]]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "No system found with IP address %s" %
                         self.net.tor_net2[0].usable[-2],
                         command)

    def testdelnotdynamic(self):
        command = ["del_dynamic_range",
                   "--startip", self.net.unknown[0].usable[7],
                   "--endip", self.net.unknown[0].usable[8]]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The range contains non-dynamic systems",
                         command)
        self.matchoutput(out,
                         "unittest12.aqd-unittest.ms.com [%s]" %
                         self.net.unknown[0].usable[7],
                         command)
        self.matchoutput(out,
                         "unittest12r.aqd-unittest.ms.com [%s]" %
                         self.net.unknown[0].usable[8],
                         command)

    def testdelrange(self):
        for ip in range(int(self.net.tor_net2[0].usable[2]),
                        int(self.net.tor_net2[0].usable[-3]) + 1):
            self.dsdb_expect_delete(IPv4Address(ip))
        command = ["del_dynamic_range",
                   "--startip", self.net.tor_net2[0].usable[2],
                   "--endip", self.net.tor_net2[0].usable[-3]]
        self.noouttest(command)
        self.dsdb_verify()

    def testverifydelrange(self):
        command = "search_system --type=dynamic_stub"
        self.noouttest(command.split(" "))

    def testdelendingrange(self):
        self.dsdb_expect_delete(self.net.tor_net2[1].usable[-1])
        command = ["del_dynamic_range",
                   "--startip", self.net.tor_net2[1].usable[-1],
                   "--endip", self.net.tor_net2[1].usable[-1]]
        self.noouttest(command)
        self.dsdb_verify()

    def testclearnetwork(self):
        for ip in range(int(self.net.tor_net2[5].usable[0]),
                        int(self.net.tor_net2[5].usable[-1]) + 1):
            self.dsdb_expect_delete(IPv4Address(ip))
        command = ["del_dynamic_range",
                   "--clearnetwork", self.net.tor_net2[5].ip]
        self.noouttest(command)
        self.dsdb_verify()

    def testclearnetworkagain(self):
        command = ["del_dynamic_range",
                   "--clearnetwork", self.net.tor_net2[5].ip]
        out = self.badrequesttest(command)
        self.matchoutput(out, "No dynamic stubs found on network.", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelDynamicRange)
    unittest.TextTestRunner(verbosity=2).run(suite)

