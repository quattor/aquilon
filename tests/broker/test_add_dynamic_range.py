#!/usr/bin/env python2.5
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009  Contributor
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
"""Module for testing the add dynamic range command."""


import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestAddDynamicRange(TestBrokerCommand):

    def testadddifferentnetworks(self):
        # Should probably add a network with add_network and then use it here.
        command = ["add_dynamic_range",
                   "--startip=%s" % self.dynamic_range_start,
                   "--endip=8.8.12.1", "--dns_domain=aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "must be on the same subnet", command)

    def testaddmissingdomain(self):
        command = ["add_dynamic_range",
                   "--startip=%s" % self.dynamic_range_start,
                   "--endip=%s" % self.dynamic_range_end,
                   "--dns_domain=dns_domain_does_not_exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "DNS Domain 'dns_domain_does_not_exist' not found",
                         command)

    def testalreadytaken(self):
        command = ["add_dynamic_range",
                   "--startip=%s" % self.hostip12,
                   "--endip=%s" % self.hostip13,
                   "--prefix=oops",
                   "--dns_domain=aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "the following hosts already exist", command)
        self.matchoutput(out,
                         "unittest12.aqd-unittest.ms.com (%s)" % self.hostip12,
                         command)
        self.matchoutput(out,
                         "unittest12r.aqd-unittest.ms.com (%s)" %
                         self.hostip13,
                         command)

    def testaddrange(self):
        command = ["add_dynamic_range",
                   "--startip=%s" % self.dynamic_range_start,
                   "--endip=%s" % self.dynamic_range_end,
                   "--dns_domain=aqd-unittest.ms.com"]
        self.noouttest(command)

    def testverifyrange(self):
        command = "search_system --type=dynamic_stub"
        out = self.commandtest(command.split(" "))
        # Assume that first three octets are the same.
        s = self.dynamic_range_start.split('.')
        end = self.dynamic_range_end.split('.')
        checked = False
        for i in range(int(s[-1]), int(end[-1]) + 1):
            checked = True
            dynamic_host = "dynamic-%s-%s-%s-%s.aqd-unittest.ms.com" % \
                    (s[0], s[1], s[2], i)
            self.matchoutput(out, dynamic_host, command)
            subcommand = ["search_system",
                          "--ip=%s.%s.%s.%s" % (s[0], s[1], s[2], i),
                          "--fqdn=%s" % dynamic_host]
            subout = self.commandtest(subcommand)
            self.matchoutput(subout, dynamic_host, command)
        self.failUnless(checked, "Problem with test algorithm or data.")


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddDynamicRange)
    unittest.TextTestRunner(verbosity=2).run(suite)

