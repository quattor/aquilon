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
"""Module for testing the add address command."""


import os
import sys
import unittest
from ipaddr import IPv4Address

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.6"))

from brokertest import TestBrokerCommand


class TestAddAddress(TestBrokerCommand):

    def test_100_basic(self):
        self.dsdb_expect_add("arecord13.aqd-unittest.ms.com",
                             self.net.unknown[0].usable[13])
        command = ["add_address", "--ip=%s" % self.net.unknown[0].usable[13],
                   "--fqdn=arecord13.aqd-unittest.ms.com"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_150_verifybasic(self):
        command = ["show_fqdn", "--fqdn=arecord13.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "DNS Record: arecord13.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "IP: %s" % self.net.unknown[0].usable[13],
                         command)

    def test_200_env(self):
        self.dsdb_expect_add("arecord14.aqd-unittest.ms.com",
                             self.net.unknown[0].usable[14])
        default = self.config.get("broker", "default_dns_environment")
        command = ["add_address", "--ip=%s" % self.net.unknown[0].usable[14],
                   "--fqdn=arecord14.aqd-unittest.ms.com",
                   "--dns_environment=%s" % default]
        self.noouttest(command)
        self.dsdb_verify()

    def test_250_verifyenv(self):
        command = ["show_fqdn", "--fqdn=arecord14.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "DNS Record: arecord14.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "IP: %s" % self.net.unknown[0].usable[14],
                         command)

    def test_300_ipfromip(self):
        self.dsdb_expect_add("arecord15.aqd-unittest.ms.com",
                             self.net.unknown[0].usable[15])
        command = ["add_address", "--ipalgorithm=max",
                   "--ipfromip=%s" % self.net.unknown[0].ip,
                   "--fqdn=arecord15.aqd-unittest.ms.com"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_350_verifyipfromip(self):
        command = ["show_fqdn", "--fqdn=arecord15.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "DNS Record: arecord15.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "IP: %s" % self.net.unknown[0].usable[15],
                         command)

    def test_900_failbadenv(self):
        default = self.config.get("broker", "default_dns_environment")
        command = ["add_address", "--ip=%s" % self.net.unknown[0].usable[16],
                   "--fqdn=arecord16.aqd-unittest.ms.com",
                   "--dns_environment=environment-does-not-exist"]
        out = self.unimplementederrortest(command)
        self.matchoutput(out,
                         "Only the '%s' DNS environment is currently "
                         "supported." % default,
                         command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddAddress)
    unittest.TextTestRunner(verbosity=2).run(suite)
