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
"""Module for testing the add vlan command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand

default_vlans = {
    701: {"name": "storage-v701",
          "type": "storage"},
    702: {"name": "vmotion-v702",
          "type": "vmotion"},
    710: {"name": "user-v710",
          "type": "user"},
    711: {"name": "user-v711",
          "type": "user"},
    712: {"name": "user-v712",
          "type": "user"},
    713: {"name": "user-v713",
          "type": "user"},
    714: {"name": "user-v714",
          "type": "user"},
    999: {"name": "unused-v999",
          "type": "user"},
}


class TestAddVlan(TestBrokerCommand):
    def test_100_add_default_vlans(self):
        for vlan_id, params in default_vlans.items():
            self.noouttest(["add_vlan", "--vlan", vlan_id,
                            "--name", params["name"],
                            "--vlan_type", params["type"]])

            command = ["show_vlan", "--vlan", vlan_id]
            out = self.commandtest(command)
            self.matchoutput(out, "VLAN: %s" % vlan_id, command)
            self.matchoutput(out, "Name: %s" % params["name"], command)
            self.matchoutput(out, "Type: %s" % params["type"], command)

    def test_200_add_again(self):
        command = ["add_vlan", "--vlan", "701", "--name", "storage-v701",
                   "--vlan_type", "storage"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "VlanInfo 701 already exists.", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddVlan)
    unittest.TextTestRunner(verbosity=2).run(suite)
