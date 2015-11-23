#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013,2015  Contributor
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
"""Module for testing the add cpu command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest
from brokertest import TestBrokerCommand


class TestAddCpu(TestBrokerCommand):

    def test_100_add_utcpu(self):
        command = ["add", "cpu", "--cpu", "utcpu", "--vendor", "intel",
                   "--comments", "Some CPU comments"]
        self.statustest(command)

    def test_105_show_utcpu(self):
        command = "show cpu --cpu utcpu --vendor intel"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Vendor: intel Model: utcpu", command)
        self.matchoutput(out, "Model Type: cpu", command)
        self.matchoutput(out, "Comments: Some CPU comments", command)

    def test_110_add_utcpu_1500(self):
        command = "add cpu --cpu utcpu_1500 --vendor intel"
        self.statustest(command.split(" "))

    def test_115_show_utcpu_1500(self):
        command = "show cpu --cpu utcpu_1500"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Vendor: intel Model: utcpu_1500", command)

    def test_120_add_unused_cpu(self):
        # A CPU model that should not be used by any machines
        self.noouttest(["add_model", "--type", "cpu", "--model", "unused",
                        "--vendor", "utvendor"])

    def test_200_add_utcpu_again(self):
        command = ["add", "cpu", "--cpu", "utcpu", "--vendor", "intel",
                   "--comments", "Some CPU comments"]
        self.badrequesttest(command)

    def test_300_show_all(self):
        command = ["show_cpu", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Vendor: intel Model: utcpu", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddCpu)
    unittest.TextTestRunner(verbosity=2).run(suite)
