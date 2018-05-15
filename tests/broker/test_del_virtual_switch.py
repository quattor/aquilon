#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2012,2013,2014,2015,2016  Contributor
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

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelVirtualSwitch(TestBrokerCommand):
    def test_100_unregister_pg_tag(self):
        self.noouttest(["unbind_port_group", "--virtual_switch", "utvswitch",
                        "--tag", "710"])

    def test_102_unbind_pg_custom_type(self):
        net = self.net["autopg3"]
        command = ["unbind_port_group", "--virtual_switch", "utvswitch",
                   "--networkip", net.ip]
        self.noouttest(command)

    def test_105_verify_pg_gone(self):
        command = ["show_virtual_switch", "--virtual_switch", "utvswitch"]
        out = self.commandtest(command)
        self.matchclean(out, "Port Group", command)

    def test_110_del_utvswitch(self):
        command = ["del_virtual_switch", "--virtual_switch", "utvswitch"]
        self.noouttest(command)

    def test_115_verify_utvswitch(self):
        command = ["show_virtual_switch", "--virtual_switch", "utvswitch"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Virtual Switch utvswitch not found.", command)

    def test_120_del_utvswitch2(self):
        command = ["del_virtual_switch", "--virtual_switch", "utvswitch2"]
        self.noouttest(command)

    def test_130_del_camelcase(self):
        self.check_plenary_exists("virtualswitchdata", "camelcase")
        self.noouttest(["del_virtual_switch", "--virtual_switch", "CaMeLcAsE"])
        self.check_plenary_gone("virtualswitchdata", "camelcase")

    def test_200_del_again(self):
        command = ["del_virtual_switch", "--virtual_switch", "utvswitch"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Virtual Switch utvswitch not found.", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelVirtualSwitch)
    unittest.TextTestRunner(verbosity=2).run(suite)
