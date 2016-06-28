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
"""Module for testing cluster behavior before VMs are added."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestClusterConstraintsNoVMs(TestBrokerCommand):

    def test_100_utmc4_old_location(self):
        for i in range(5, 11):
            command = ["show_cluster", "--cluster=utecl%d" % i]
            out = self.commandtest(command)
            self.matchoutput(out, "Building: ut", command)

    def test_111_fix_utmc4_location_switch(self):
        for i in range(5, 8):
            self.successtest(["update_cluster", "--cluster=utecl%d" % i,
                              "--switch=ut01ga2s01.aqd-unittest.ms.com",
                              "--fix_location"])
        for i in range(8, 11):
            self.noouttest(["update_cluster", "--cluster=utecl%d" % i,
                            "--switch=ut01ga2s02.aqd-unittest.ms.com",
                            "--fix_location"])

    def test_112_check_location_switch(self):
        command = ["show_esx_cluster", "--cluster=utecl5"]
        out = self.commandtest(command)
        self.matchoutput(out, "Rack: ut11", command)
        self.matchoutput(out, "Switch: ut01ga2s01.aqd-unittest.ms.com",
                         command)

        command = ["show_esx_cluster", "--cluster=utecl8"]
        out = self.commandtest(command)
        self.matchoutput(out, "Rack: ut12", command)
        self.matchoutput(out, "Switch: ut01ga2s02.aqd-unittest.ms.com",
                         command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(
        TestClusterConstraintsNoVMs)
    unittest.TextTestRunner(verbosity=2).run(suite)
