#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014  Contributor
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
"""Module for testing the del network device command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestDelVirtualSwitch(TestBrokerCommand):
    def test_100_del_utvswitch(self):
        command = ["del_virtual_switch", "--virtual_switch", "utvswitch"]
        self.noouttest(command)

    def test_105_verify_utvswitch(self):
        command = ["show_virtual_switch", "--virtual_switch", "utvswitch"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Virtual Switch utvswitch not found.", command)

    def test_110_del_utvswitch2(self):
        command = ["del_virtual_switch", "--virtual_switch", "utvswitch2"]
        self.noouttest(command)

    def test_200_del_again(self):
        command = ["del_virtual_switch", "--virtual_switch", "utvswitch"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Virtual Switch utvswitch not found.", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelVirtualSwitch)
    unittest.TextTestRunner(verbosity=2).run(suite)
