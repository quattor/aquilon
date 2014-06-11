#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013,2014  Contributor
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
"""Module for testing the add vlan command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand
from test_add_vlan import default_vlans


class TestDelVlan(TestBrokerCommand):
    def test_100_delete_defaults(self):
        for vlan_id in default_vlans.keys():
            self.noouttest(["del_vlan", "--vlan", vlan_id])
            self.notfoundtest(["show_vlan", "--vlan", vlan_id])

    def test_200_delete_unknown(self):
        command = ["del_vlan", "--vlan", "998"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "No port group found for VLAN id 998.", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelVlan)
    unittest.TextTestRunner(verbosity=2).run(suite)
