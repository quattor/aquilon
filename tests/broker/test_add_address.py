#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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

if __name__ == "__main__":
    import utils
    utils.import_depends()

from ipaddr import IPv4Address
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
        net = self.net.unknown[0]
        command = ["show_address", "--fqdn=arecord13.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "DNS Record: arecord13.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "IP: %s" % net.usable[13], command)
        self.matchoutput(out, "Network: %s [%s]" % (net.ip, net), command)
        self.matchoutput(out, "Network Environment: internal", command)
        self.matchclean(out, "Reverse", command)

    def test_200_add_defaultenv(self):
        self.dsdb_expect_add("arecord14.aqd-unittest.ms.com",
                             self.net.unknown[0].usable[14])
        default = self.config.get("site", "default_dns_environment")
        command = ["add_address", "--ip=%s" % self.net.unknown[0].usable[14],
                   "--fqdn=arecord14.aqd-unittest.ms.com",
                   "--reverse_ptr=arecord13.aqd-unittest.ms.com",
                   "--dns_environment=%s" % default]
        self.noouttest(command)
        self.dsdb_verify()

    def test_210_add_utenv_noreverse(self):
        # The reverse does not exist in this environment
        command = ["add_address", "--ip", self.net.unknown[1].usable[14],
                   "--fqdn", "arecord14.aqd-unittest.ms.com",
                   "--reverse_ptr", "arecord13.aqd-unittest.ms.com",
                   "--dns_environment", "ut-env"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "DNS Record arecord13.aqd-unittest.ms.com, "
                         "DNS environment ut-env not found.", command)

    def test_220_add_utenv(self):
        # Different IP in this environment
        command = ["add_address", "--ip", self.net.unknown[1].usable[14],
                   "--fqdn", "arecord14.aqd-unittest.ms.com",
                   "--dns_environment", "ut-env"]
        self.noouttest(command)

    def test_230_verifydefaultenv(self):
        default = self.config.get("site", "default_dns_environment")
        command = ["show_address", "--fqdn=arecord14.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "DNS Record: arecord14.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "DNS Environment: %s" % default, command)
        self.matchoutput(out, "IP: %s" % self.net.unknown[0].usable[14],
                         command)
        self.matchoutput(out, "Reverse PTR: arecord13.aqd-unittest.ms.com",
                         command)

    def test_230_verifyutenv(self):
        command = ["show_address", "--fqdn=arecord14.aqd-unittest.ms.com",
                   "--dns_environment", "ut-env"]
        out = self.commandtest(command)
        self.matchoutput(out, "DNS Record: arecord14.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "DNS Environment: ut-env", command)
        self.matchoutput(out, "IP: %s" % self.net.unknown[1].usable[14],
                         command)
        self.matchclean(out, "Reverse", command)

    def test_300_ipfromip(self):
        self.dsdb_expect_add("arecord15.aqd-unittest.ms.com",
                             self.net.unknown[0].usable[15])
        command = ["add_address", "--ipalgorithm=max",
                   "--ipfromip=%s" % self.net.unknown[0].ip,
                   "--fqdn=arecord15.aqd-unittest.ms.com"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_350_verifyipfromip(self):
        command = ["show_address", "--fqdn=arecord15.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "DNS Record: arecord15.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "IP: %s" % self.net.unknown[0].usable[15],
                         command)
        self.matchclean(out, "Reverse", command)

    def test_400_dsdbfailure(self):
        self.dsdb_expect_add("arecord16.aqd-unittest.ms.com",
                             self.net.unknown[0].usable[16], fail=True)
        command = ["add_address", "--ip", self.net.unknown[0].usable[16],
                   "--fqdn", "arecord16.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Could not add address to DSDB", command)
        self.dsdb_verify()

    def test_410_verifydsdbfailure(self):
        command = ["search", "dns", "--fqdn", "arecord16.aqd-unittest.ms.com"]
        self.notfoundtest(command)

    def test_420_failnetaddress(self):
        ip = self.net.unknown[0].ip
        command = ["add", "address", "--fqdn", "netaddress.aqd-unittest.ms.com",
                   "--ip", ip]
        out = self.badrequesttest(command)
        self.matchoutput(out, "IP address %s is the address of network " % ip,
                         command)

    def test_430_failbroadcast(self):
        ip = self.net.unknown[0].broadcast
        command = ["add", "address", "--fqdn", "broadcast.aqd-unittest.ms.com",
                   "--ip", ip]
        out = self.badrequesttest(command)
        self.matchoutput(out, "IP address %s is the broadcast address of "
                         "network " % ip, command)

    def test_440_failbadenv(self):
        ip = self.net.unknown[0].usable[16]
        command = ["add", "address", "--fqdn", "no-such-env.aqd-unittest.ms.com",
                   "--ip", ip, "--dns_environment", "no-such-env"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "DNS Environment no-such-env not found.", command)

    def test_450_add_too_long_name(self):
        ip = self.net.unknown[0].usable[16]
        cmd = ['add', 'address', '--fqdn',
            #          1         2         3         4         5         6
            's234567890123456789012345678901234567890123456789012345678901234' +
            '.aqd-unittest.ms.com', '--dns_environment', 'internal', '--ip', ip]
        out = self.badrequesttest(cmd)
        self.matchoutput(out,
                         "DNS name components must have a length between 1 and 63.",
                         cmd)

    def test_455_add_invalid_name(self):
        ip = self.net.unknown[0].usable[16]
        command = ['add', 'address', '--fqdn', 'foo-.aqd-unittest.ms.com',
                   '--dns_environment', 'internal', '--ip', ip]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Illegal DNS name format 'foo-'.", command)

    def test_460_restricted_domain(self):
        ip = self.net.unknown[0].usable[-1]
        command = ["add", "address", "--fqdn", "foo.restrict.aqd-unittest.ms.com",
                   "--ip", ip]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "DNS Domain restrict.aqd-unittest.ms.com is "
                         "restricted, adding extra addresses is not allowed.",
                         command)

    def test_500_addunittest20eth1(self):
        ip = self.net.unknown[12].usable[0]
        fqdn = "unittest20-e1.aqd-unittest.ms.com"
        self.dsdb_expect_add(fqdn, ip)
        command = ["add", "address", "--ip", ip, "--fqdn", fqdn]
        self.noouttest(command)
        self.dsdb_verify()

    def test_600_addip_with_network_env(self):
        ip = "192.168.3.1"
        fqdn = "cardenvtest600.aqd-unittest.ms.com"
        command = ["add", "address", "--ip", ip, "--fqdn", fqdn,
                   "--network_environment", "cardenv"]
        self.noouttest(command)
        # External IP addresses should not be added to DSDB
        self.dsdb_verify(empty=True)

        command = ["show_address", "--fqdn=%s" % fqdn,
                   "--network_environment", "cardenv"]
        out = self.commandtest(command)
        self.matchoutput(out, "DNS Record: %s" % fqdn,
                         command)
        self.matchoutput(out, "IP: %s" % ip,
                         command)
        self.matchoutput(out, "DNS Environment: ut-env", command)
        self.matchoutput(out, "Network Environment: cardenv", command)

    def test_610_addipfromip_with_network_env(self):
        fqdn = "cardenvtest610.aqd-unittest.ms.com"
        command = ["add", "address", "--ipfromip", "192.168.3.0",
                   "--fqdn", fqdn, "--network_environment", "cardenv"]
        self.noouttest(command)
        # External IP addresses should not be added to DSDB
        self.dsdb_verify(empty=True)

        command = ["show_address", "--fqdn=%s" % fqdn,
                   "--network_environment", "cardenv"]
        out = self.commandtest(command)
        self.matchoutput(out, "DNS Record: %s" % fqdn,
                         command)
        self.matchoutput(out, "IP: %s" % "192.168.3.5",
                         command)
        self.matchoutput(out, "DNS Environment: ut-env", command)
        self.matchoutput(out, "Network Environment: cardenv", command)

    def test_620_addexternalip_in_interanldns(self):
        ip = "192.168.3.4"
        fqdn = "cardenvtest620.aqd-unittest.ms.com"
        default = self.config.get("site", "default_dns_environment")
        command = ["add", "address", "--ip", ip, "--fqdn", fqdn,
                   "--dns_environment", default,
                   "--network_environment", "cardenv"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Entering external IP addresses to the internal DNS environment is not allowed", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddAddress)
    unittest.TextTestRunner(verbosity=2).run(suite)
