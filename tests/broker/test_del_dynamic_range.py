#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
                   "--startip", self.net["dyndhcp0"].usable[2],
                   "--endip", self.net["dyndhcp1"].usable[2]]
        out = self.badrequesttest(command)
        self.matchoutput(out, "must be on the same subnet", command)

    # These rely on the ip never having been used...
    def testdelnothingfound(self):
        command = ["del_dynamic_range",
                   "--startip", self.net["dyndhcp0"].usable[-2],
                   "--endip", self.net["dyndhcp0"].usable[-1]]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Nothing found in range", command)

    def testdelnostart(self):
        command = ["del_dynamic_range",
                   "--startip", self.net["dyndhcp0"].usable[1],
                   "--endip", self.net["dyndhcp0"].usable[-3]]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "No system found with IP address %s" %
                         self.net["dyndhcp0"].usable[1],
                         command)

    def testdelnoend(self):
        command = ["del_dynamic_range",
                   "--startip", self.net["dyndhcp0"].usable[2],
                   "--endip", self.net["dyndhcp0"].usable[-2]]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "No system found with IP address %s" %
                         self.net["dyndhcp0"].usable[-2],
                         command)

    def testdelnotdynamic(self):
        command = ["del_dynamic_range",
                   "--startip", self.net["unknown0"].usable[7],
                   "--endip", self.net["unknown0"].usable[8]]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The range contains non-dynamic systems",
                         command)
        self.matchoutput(out,
                         "unittest12.aqd-unittest.ms.com [%s]" %
                         self.net["unknown0"].usable[7],
                         command)
        self.matchoutput(out,
                         "unittest12r.aqd-unittest.ms.com [%s]" %
                         self.net["unknown0"].usable[8],
                         command)

    def testdelrange(self):
        messages = []
        for ip in range(int(self.net["dyndhcp0"].usable[2]),
                        int(self.net["dyndhcp0"].usable[-3]) + 1):
            address = IPv4Address(ip)
            self.dsdb_expect_delete(address)
            messages.append("DSDB: delete_host -ip_address %s" % address)
        command = ["del_dynamic_range",
                   "--startip", self.net["dyndhcp0"].usable[2],
                   "--endip", self.net["dyndhcp0"].usable[-3]]
        err = self.statustest(command)
        for message in messages:
            self.matchoutput(err, message, command)
        self.dsdb_verify()

    def testverifydelrange(self):
        command = "search_dns --record_type=dynamic_stub"
        self.noouttest(command.split(" "))

    def testdelendingrange(self):
        ip = self.net["dyndhcp1"].usable[-1]
        self.dsdb_expect_delete(ip)
        command = ["del_dynamic_range", "--startip", ip, "--endip", ip]
        err = self.statustest(command)
        self.matchoutput(err, "DSDB: delete_host -ip_address %s" % ip, command)
        self.dsdb_verify()

    def testclearnetwork(self):
        messages = []
        for ip in range(int(self.net["dyndhcp3"].usable[0]),
                        int(self.net["dyndhcp3"].usable[-1]) + 1):
            address = IPv4Address(ip)
            self.dsdb_expect_delete(address)
            messages.append("DSDB: delete_host -ip_address %s" % address)
        command = ["del_dynamic_range",
                   "--clearnetwork", self.net["dyndhcp3"].ip]
        err = self.statustest(command)
        for message in messages:
            self.matchoutput(err, message, command)
        self.dsdb_verify()

    def testclearnetworkagain(self):
        command = ["del_dynamic_range",
                   "--clearnetwork", self.net["dyndhcp3"].ip]
        out = self.badrequesttest(command)
        self.matchoutput(out, "No dynamic stubs found on network.", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelDynamicRange)
    unittest.TextTestRunner(verbosity=2).run(suite)
