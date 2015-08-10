#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014,2015  Contributor
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
"""Module for testing the del metacluster command."""

from datetime import datetime
import os

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand
from notificationtest import VerifyNotificationsMixin


class TestDelMetaCluster(VerifyNotificationsMixin, TestBrokerCommand):

    def test_100_del_utmc1(self):
        basetime = datetime.now()
        command = ["del_metacluster", "--metacluster=utmc1"]
        self.statustest(command)
        self.wait_notification(basetime, 0)

    def test_105_verify_utmc1(self):
        command = ["show_metacluster", "--metacluster=utmc1"]
        self.notfoundtest(command)

    def test_110_del_utmc2(self):
        basetime = datetime.now()
        command = ["del_metacluster", "--metacluster=utmc2"]
        self.statustest(command)
        self.wait_notification(basetime, 0)

    def test_115_verify_utmc2(self):
        command = ["show_metacluster", "--metacluster=utmc2"]
        self.notfoundtest(command)

    def test_120_del_utmc3(self):
        basetime = datetime.now()
        command = ["del_metacluster", "--metacluster=utmc3"]
        self.statustest(command)
        self.wait_notification(basetime, 0)

    def test_130_del_utmc4(self):
        basetime = datetime.now()
        command = ["del_metacluster", "--metacluster=utmc4"]
        self.statustest(command)
        self.wait_notification(basetime, 0)

    def test_140_del_utmc7(self):
        basetime = datetime.now()
        command = ["del_metacluster", "--metacluster=utmc7"]
        self.statustest(command)
        self.wait_notification(basetime, 0)

    def test_150_del_sandboxmc(self):
        # Test moving machines between metaclusters
        basetime = datetime.now()
        command = ["del_metacluster", "--metacluster=sandboxmc"]
        self.statustest(command)
        self.wait_notification(basetime, 0)

    def test_160_del_vulcan1(self):
        basetime = datetime.now()
        command = ["del_metacluster", "--metacluster=vulcan1"]
        self.statustest(command)
        self.wait_notification(basetime, 0)

    def test_160_del_utmc8(self):
        self.statustest(["del_metacluster", "--metacluster=utmc8"])

        self.assertFalse(os.path.exists(os.path.join(
            self.config.get("broker", "profilesdir"), "clusters",
            "utmc8" + self.xml_suffix)))

    def test_165_del_utmc9(self):
        command = ["del_metacluster", "--metacluster=utmc9"]
        self.statustest(command)

        self.assertFalse(os.path.exists(os.path.join(
            self.config.get("broker", "profilesdir"), "clusters",
            "utmc9" + self.xml_suffix)))

    def test_200_del_nonexistant(self):
        command = ["del_metacluster",
                   "--metacluster=metacluster-does-not-exist"]
        self.notfoundtest(command)

    def test_300_show_all(self):
        command = ["show_metacluster", "--all"]
        out = self.commandtest(command)
        self.matchclean(out, "utmc", command)
        self.matchclean(out, "sandboxmc", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelMetaCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
