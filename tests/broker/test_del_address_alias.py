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
"""Module for testing the del address alias command."""

if __name__ == '__main__':
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestDelAddressAlias(TestBrokerCommand):

    def test_100_del_addralias_with_target(self):
        command = ["del", "address", "alias",
                   "--fqdn", "addralias1.aqd-unittest.ms.com",
                   "--target", "arecord13.aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_150_verify_del_addralias_with_target(self):
        command = ["search", "dns",
                   "--fqdn", "addralias1.aqd-unittest.ms.com",
                   "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "Address Alias: addralias1.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "DNS Environment: internal", command)
        self.matchoutput(out, "Target: arecord14.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Target: arecord15.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Comments: Some other address alias comments",
                         command)

    def test_200_del_addralias_with_nonexistent_target(self):
        command = ["del", "address", "alias",
                   "--fqdn", "addralias1.aqd-unittest.ms.com",
                   "--target", "arecord13.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Address Alias addralias1.aqd-unittest.ms.com, "
                         "with target arecord13.aqd-unittest.ms.com not found.",
                         command)

    def test_250_del_addralias_of_other_type(self):
        command = ["del", "address", "alias",
                   "--fqdn", "arecord13.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Address Alias arecord13.aqd-unittest.ms.com "
                         "not found.", command)

    def test_400_del_addralias(self):
        command = ["del", "address", "alias",
                   "--fqdn", "addralias1.aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_450_verify_del_addralias(self):
        command = ["search", "dns",
                   "--fqdn", "addralias1.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Fqdn addralias1, DNS environment internal, "
                         "DNS domain aqd-unittest.ms.com not found.",
                         command)

    def test_500_del_cross_environment(self):
        command = ["del", "address", "alias",
                   "--fqdn", "addralias1.aqd-unittest-ut-env.ms.com",
                   "--dns_environment", "ut-env",
                   "--target", "arecord13.aqd-unittest.ms.com",
                   "--target_environment", "internal"]
        self.noouttest(command)

    def test_550_verify_del_cross_environment(self):
        command = ["search", "dns",
                   "--fqdn", "addralias1.aqd-unittest-ut-env.ms.com",
                   "--dns_environment", "ut-env"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Fqdn addralias1, DNS environment ut-env, "
                         "DNS domain aqd-unittest-ut-env.ms.com not found.",
                         command)

    def test_600_del_addralias_with_grn(self):
        command = ["del", "address", "alias",
                   "--fqdn", "addralias3.aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_605_verify_del_addralias_with_grn(self):
        command = ["search", "dns",
                   "--fqdn", "addralias3.aqd-unittest.ms.com"]
        self.notfoundtest(command)

    def test_610_del_addralias_with_grn(self):
        command = ["del", "address", "alias",
                   "--fqdn", "addralias4.aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_615_verify_del_addralias_with_grn(self):
        command = ["search", "dns",
                   "--fqdn", "addralias4.aqd-unittest.ms.com"]
        self.notfoundtest(command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelAddressAlias)
    unittest.TextTestRunner(verbosity=2).run(suite)
