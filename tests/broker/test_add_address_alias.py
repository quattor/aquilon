#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015  Contributor
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
"""Module for testing the add address alias command."""

if __name__ == '__main__':
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestAddAddressAlias(TestBrokerCommand):

    def test_100_add_addralias(self):
        command = ["add", "address", "alias",
                   "--fqdn", "addralias1.aqd-unittest.ms.com",
                   "--target", "arecord13.aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_110_add_addralias_dupliate(self):
        command = ["add", "address", "alias",
                   "--fqdn", "addralias1.aqd-unittest.ms.com",
                   "--target", "arecord13.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Address Alias addralias1.aqd-unittest.ms.com "
                         "with target arecord13.aqd-unittest.ms.com "
                         "already exists.", command)

    def test_150_verify_addralias(self):
        command = ["search", "dns",
                   "--fqdn", "addralias1.aqd-unittest.ms.com",
                   "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "Address Alias: addralias1.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "DNS Environment: internal", command)
        self.matchoutput(out,
                         "Target: arecord13.aqd-unittest.ms.com [%s]" %
                         self.net["unknown0"].usable[13], command)

    def test_200_add_new_addralias_with_comment(self):
        command = ["add", "address", "alias",
                   "--fqdn", "addralias1.aqd-unittest.ms.com",
                   "--target", "arecord14.aqd-unittest.ms.com",
                   "--dns_environment", "internal",
                   "--comments", "Some address alias comments"]
        self.noouttest(command)

    def test_200_add_new_addralias_with_comment2(self):
        command = ["add", "address", "alias",
                   "--fqdn", "addralias1.aqd-unittest.ms.com",
                   "--target", "arecord15.aqd-unittest.ms.com",
                   "--target_environment", "internal",
                   "--comments", "Some other address alias comments"]
        self.noouttest(command)

    def test_250_verify_addralias(self):
        command = ["search", "dns",
                   "--fqdn", "addralias1.aqd-unittest.ms.com",
                   "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "Address Alias: addralias1.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "DNS Environment: internal", command)
        self.matchoutput(out,
                         "Target: arecord13.aqd-unittest.ms.com [%s]" %
                         self.net["unknown0"].usable[13], command)
        self.matchoutput(out,
                         "Target: arecord14.aqd-unittest.ms.com [%s]" %
                         self.net["unknown0"].usable[14], command)
        self.matchoutput(out,
                         "Target: arecord15.aqd-unittest.ms.com [%s]" %
                         self.net["unknown0"].usable[15], command)
        self.matchoutput(out, "Comments: Some address alias comments", command)
        self.matchoutput(out, "Comments: Some other address alias comments", command)

    def test_300_add_restricted(self):
        command = ["add", "address", "alias",
                   "--fqdn", "addralias1.restrict.aqd-unittest.ms.com",
                   "--target", "arecord14.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "DNS Domain restrict.aqd-unittest.ms.com is "
                         "restricted, aliases are not allowed.", command)

    def test_400_add_ms_com(self):
        command = ["add", "address", "alias",
                   "--fqdn", "addralias1.ms.com",
                   "--target", "arecord13.aqd-unittest.ms.com",
                   "--dns_environment", "internal"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Address Alias record in DNS domain ms.com, DNS "
                         "environment internal is not allowed.",
                         command)

    def test_500_add_invalid_target(self):
        command = ["add", "address", "alias",
                   "--fqdn", "addralias2.aqd-unittest.ms.com",
                   "--target", "addralias1.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The target of each Address Alias record must resolve "
                         "to one and only one ip address", command)

    def test_600_add_cross_environment(self):
        command = ["add", "address", "alias",
                   "--fqdn", "addralias1.aqd-unittest-ut-env.ms.com",
                   "--dns_environment", "ut-env",
                   "--target", "arecord13.aqd-unittest.ms.com",
                   "--target_environment", "internal"]
        self.noouttest(command)

    def test_650_verify_cross_environment(self):
        command = ["search", "dns",
                   "--fqdn", "addralias1.aqd-unittest-ut-env.ms.com",
                   "--dns_environment", "ut-env",
                   "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Address Alias: addralias1.aqd-unittest-ut-env.ms.com",
                         command)
        self.matchoutput(out, "DNS Environment: ut-env", command)
        self.matchoutput(out,
                         "Target: arecord13.aqd-unittest.ms.com [%s, environment: internal]" %
                         self.net["unknown0"].usable[13],
                         command)

    def test_700_verify_target_output(self):
        command = ["search", "dns",
                   "--fqdn", "arecord13.aqd-unittest.ms.com", "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Address Aliases:"
                         " addralias1.aqd-unittest-ut-env.ms.com [environment: ut-env],"
                         " addralias1.aqd-unittest.ms.com",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddAddressAlias)
    unittest.TextTestRunner(verbosity=2).run(suite)
