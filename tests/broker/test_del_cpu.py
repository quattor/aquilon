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
"""Module for testing the del cpu command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest
from brokertest import TestBrokerCommand


class TestDelCpu(TestBrokerCommand):

    def test_100_del_utcpu(self):
        command = "del cpu --cpu utcpu --vendor intel"
        self.statustest(command.split(" "))

    def test_105_verify_utcpu(self):
        command = "show cpu --cpu utcpu --vendor intel"
        self.notfoundtest(command.split(" "))

    def test_110_del_utcpu_1500(self):
        command = "del cpu --cpu utcpu_1500 --vendor intel"
        self.statustest(command.split(" "))

    def test_115_verify_utcpu_1500(self):
        command = "show cpu --cpu utcpu_1500"
        self.notfoundtest(command.split(" "))

    def test_120_del_unused(self):
        self.statustest(["del_cpu", "--cpu", "unused", "--vendor", "utvendor"])

    def test_200_del_nocpu(self):
        command = ["del_cpu", "--cpu", "no-such-cpu", "--vendor", "utvendor"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Model no-such-cpu, vendor utvendor, "
                         "model_type cpu not found.",
                         command)

    def test_200_del_novendor(self):
        command = ["del_cpu", "--cpu", "no-such-cpu",
                   "--vendor", "no-such-vendor"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Vendor no-such-vendor not found.", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelCpu)
    unittest.TextTestRunner(verbosity=2).run(suite)
