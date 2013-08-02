#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
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
"""Module for testing the del feature command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestDelFeature(TestBrokerCommand):

    def test_100_del_host_pre(self):
        command = ["del", "feature", "--feature", "pre_host", "--type", "host"]
        self.noouttest(command)

    def test_100_del_host_post(self):
        command = ["del", "feature", "--feature", "post_host", "--type", "host"]
        self.noouttest(command)

    def test_100_del_hw(self):
        command = ["del", "feature", "--feature", "bios_setup",
                   "--type", "hardware"]
        self.noouttest(command)

    def test_100_del_hw2(self):
        command = ["del", "feature", "--feature", "disable_ht",
                   "--type", "hardware"]
        self.noouttest(command)

    def test_100_del_iface(self):
        command = ["del", "feature", "--feature", "src_route",
                   "--type", "interface"]
        self.noouttest(command)

    def test_110_verify_pre(self):
        command = ["show", "feature", "--feature", "pre_host", "--type", "host"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Host Feature pre_host not found.", command)

    def test_110_verify_post(self):
        command = ["show", "feature", "--feature", "post_host",
                   "--type", "host"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Host Feature post_host not found.", command)

    def test_110_verify_hw(self):
        command = ["show", "feature", "--feature", "bios_setup",
                   "--type", "hardware"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Hardware Feature bios_setup not found.", command)

    def test_110_verify_iface(self):
        command = ["show", "feature", "--feature", "src_route",
                   "--type", "interface"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Interface Feature src_route not found.", command)

    def test_120_show_all(self):
        command = ["show", "feature", "--all"]
        out = self.commandtest(command)
        self.matchclean(out, "pre_host", command)
        self.matchclean(out, "post_host", command)
        self.matchclean(out, "bios_setup", command)
        self.matchclean(out, "src_route", command)

    def test_200_del_again(self):
        command = ["del", "feature", "--feature", "bios_setup",
                   "--type", "hardware"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Hardware Feature bios_setup not found.", command)

    def test_210_del_bad_type(self):
        command = ["del", "feature", "--feature", "bad-type",
                   "--type", "no-such-type"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Unknown feature type 'no-such-type'. The "
                         "valid values are: hardware, host, interface.",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelFeature)
    unittest.TextTestRunner(verbosity=2).run(suite)
