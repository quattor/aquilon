#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013  Contributor
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
"""Module for testing the update chassis command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand
from chassistest import VerifyChassisMixin


class TestUpdateChassis(TestBrokerCommand, VerifyChassisMixin):

    def test_100_update_ut3c5(self):
        ip = self.net.unknown[0].usable[6]
        self.dsdb_expect_add("ut3c5.aqd-unittest.ms.com", ip, "oa",
                             comments="Some new chassis comments")
        command = ["update", "chassis", "--chassis", "ut3c5.aqd-unittest.ms.com",
                   "--rack", "ut3", "--serial", "ABC5678",
                   "--model", "c-class", "--ip", ip,
                   "--comments", "Some new chassis comments"]
        self.noouttest(command)

    def test_110_verify_ut3c5(self):
        self.verifychassis("ut3c5.aqd-unittest.ms.com", "hp", "c-class",
                           "ut3", "a", "3", "ABC5678",
                           comments="Some new chassis comments",
                           ip=self.net.unknown[0].usable[6])

    def test_200_update_bad_ip(self):
        ip = self.net.unknown[0].usable[6]
        command = ["update", "chassis", "--ip", ip,
                   "--chassis", "ut3c1.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                          "IP address %s is already in use by on-board admin "
                          "interface oa of chassis "
                          "ut3c5.aqd-unittest.ms.com." % ip,
                          command)

    def test_200_update_bad_model(self):
        command = ["update", "chassis", "--model", "uttorswitch",
                   "--chassis", "ut3c1.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Model uttorswitch, machine_type chassis not found.",
                         command)

    def test_200_not_chassis(self):
        command = ["update", "chassis", "--chassis",
                   "ut3gd1r01.aqd-unittest.ms.com",
                   "--comments", "Not a chassis"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Switch ut3gd1r01.aqd-unittest.ms.com exists, but "
                         "is not a chassis.",
                         command)

    def test_200_no_model(self):
        command = ["update", "chassis", "--vendor", "generic",
                   "--chassis", "ut3c1.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Model utchassis, vendor generic, "
                         "machine_type chassis not found.",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateChassis)
    unittest.TextTestRunner(verbosity=2).run(suite)
