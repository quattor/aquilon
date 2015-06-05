#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013,2014,2015  Contributor
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
"""Module for testing the update cpu command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestUpdateCpu(TestBrokerCommand):

    def test_100_clear_comments(self):
        command = ["update_cpu", "--cpu", "utcpu", "--vendor", "intel",
                   "--comments", ""]
        self.noouttest(command)

    def test_105_verify_update(self):
        command = "show cpu --cpu utcpu --vendor intel"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Comments", command)

    def test_110_update_cpu(self):
        command = ["update_cpu", "--cpu", "utcpu", "--vendor", "intel",
                   "--comments", "New CPU comments"]
        self.noouttest(command)

    def test_115_verify_update(self):
        command = "show cpu --cpu utcpu --vendor intel"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Cpu: intel utcpu", command)
        self.matchoutput(out, "Comments: New CPU comments", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateCpu)
    unittest.TextTestRunner(verbosity=2).run(suite)
