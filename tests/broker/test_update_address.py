#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013  Contributor
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
"""Module for testing the update address command."""


import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUpdateAddress(TestBrokerCommand):

    def test_100_update_reverse(self):
        self.dsdb_expect_update_address("arecord15.aqd-unittest.ms.com",
                                        comments="Test comment")
        command = ["update", "address",
                   "--fqdn", "arecord15.aqd-unittest.ms.com",
                   "--reverse_ptr", "arecord14.aqd-unittest.ms.com",
                   "--comments", "Test comment"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_105_verify_arecord15(self):
        command = ["show", "fqdn", "--fqdn", "arecord15.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Comments: Test comment", command)
        self.matchoutput(out, "Reverse PTR: arecord14.aqd-unittest.ms.com",
                         command)

    def test_105_search_ptr(self):
        command = ["search", "dns",
                   "--reverse_ptr", "arecord14.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "arecord15.aqd-unittest.ms.com", command)

    def test_105_search_override(self):
        command = ["search", "dns", "--reverse_override"]
        out = self.commandtest(command)
        self.matchoutput(out, "arecord15.aqd-unittest.ms.com", command)

    def test_110_clear_ptr_override(self):
        command = ["update", "address",
                   "--fqdn", "arecord15.aqd-unittest.ms.com",
                   "--reverse_ptr", "arecord15.aqd-unittest.ms.com"]
        self.noouttest(command)
        self.dsdb_verify(empty=True)

    def test_115_verify_arecord15(self):
        command = ["show", "fqdn", "--fqdn", "arecord15.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "Reverse", command)

    def test_115_verify_search(self):
        command = ["search", "dns", "--reverse_override"]
        out = self.commandtest(command)
        self.matchclean(out, "arecord15.aqd-unittest.ms.com", command)

    #def test_120_update_ip(self):
    #    old_ip = self.net.unknown[0].usable[15]
    #    ip = self.net.unknown[0].usable[-1]
    #    self.dsdb_expect_delete(old_ip)
    #    self.dsdb_expect_add("arecord15.aqd-unittest.ms.com", ip,
    #                         comments="Test comment")
    #    command = ["update", "address",
    #               "--fqdn", "arecord15.aqd-unittest.ms.com", "--ip", ip]
    #    self.noouttest(command)
    #    self.dsdb_verify()

    #def test_125_verify_arecord15(self):
    #    ip = self.net.unknown[0].usable[-1]
    #    command = ["show", "fqdn", "--fqdn", "arecord15.aqd-unittest.ms.com"]
    #    out = self.commandtest(command)
    #    self.matchoutput(out, "IP: %s" % ip, command)

    #def test_129_fix_ip(self):
    #    # Change the IP address back not to confuse other parts of the testsuite
    #    old_ip = self.net.unknown[0].usable[-1]
    #    ip = self.net.unknown[0].usable[15]
    #    self.dsdb_expect_delete(old_ip)
    #    self.dsdb_expect_add("arecord15.aqd-unittest.ms.com", ip,
    #                         comments="Test comment")
    #    command = ["update", "address",
    #               "--fqdn", "arecord15.aqd-unittest.ms.com", "--ip", ip]
    #    self.noouttest(command)
    #    self.dsdb_verify()

    def test_130_update_dyndhcp_noop(self):
        command = ["update", "address",
                   "--fqdn", "dynamic-4-2-4-20.aqd-unittest.ms.com",
                   "--reverse_ptr", "dynamic-4-2-4-20.aqd-unittest.ms.com"]
        self.noouttest(command)
        self.dsdb_verify(empty=True)

    def test_135_verify_dyndhcp(self):
        command = ["show", "fqdn", "--fqdn",
                   "dynamic-4-2-4-20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "Reverse", command)

    def test_200_update_dyndhcp(self):
        command = ["update", "address",
                   "--fqdn", "dynamic-4-2-4-20.aqd-unittest.ms.com",
                   "--reverse_ptr", "unittest20.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The reverse PTR record cannot be set for DNS "
                         "records used for dynamic DHCP.", command)

    #def test_200_ip_conflict(self):
    #    ip = self.net.unknown[0].usable[14]
    #    command = ["update", "address",
    #               "--fqdn", "arecord15.aqd-unittest.ms.com", "--ip", ip]
    #    out = self.badrequesttest(command)
    #    self.matchoutput(out, "IP address %s is already used by DNS record "
    #                     "arecord14.aqd-unittest.ms.com." % ip, command)

    #def test_200_update_primary(self):
    #    command = ["update", "address",
    #               "--fqdn", "unittest20.aqd-unittest.ms.com",
    #               "--ip", self.net.unknown[0].usable[-1]]
    #    out = self.badrequesttest(command)
    #    self.matchoutput(out, "DNS Record unittest20.aqd-unittest.ms.com is "
    #                     "a primary name, and its IP address cannot be "
    #                     "changed.", command)

    #def test_200_update_used(self):
    #    command = ["update", "address",
    #               "--fqdn", "unittest20-e1.aqd-unittest.ms.com",
    #               "--ip", self.net.unknown[0].usable[-1]]
    #    out = self.badrequesttest(command)
    #    self.matchoutput(out, "DNS Record unittest20-e1.aqd-unittest.ms.com is "
    #                     "already used by the following interfaces, and its "
    #                     "IP address cannot be changed: "
    #                     "unittest20.aqd-unittest.ms.com/eth1.",
    #                     command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateAddress)
    unittest.TextTestRunner(verbosity=2).run(suite)
