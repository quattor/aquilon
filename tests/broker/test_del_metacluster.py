#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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


import unittest
from datetime import datetime

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand
from notificationtest import VerifyNotificationsMixin


class TestDelMetaCluster(VerifyNotificationsMixin, TestBrokerCommand):

    def testdelutmc1(self):
        basetime = datetime.now()
        command = ["del_metacluster", "--metacluster=utmc1"]
        self.statustest(command)
        self.wait_notification(basetime, 0)

    def testverifydelutmc1(self):
        command = ["show_metacluster", "--metacluster=utmc1"]
        self.notfoundtest(command)

    def testdelutmc2(self):
        basetime = datetime.now()
        command = ["del_metacluster", "--metacluster=utmc2"]
        self.statustest(command)
        self.wait_notification(basetime, 0)

    def testverifydelutmc2(self):
        command = ["show_metacluster", "--metacluster=utmc2"]
        self.notfoundtest(command)

    def testdelutmc3(self):
        basetime = datetime.now()
        command = ["del_metacluster", "--metacluster=utmc3"]
        self.statustest(command)
        self.wait_notification(basetime, 0)

    def testverifydelutmc3(self):
        command = ["show_metacluster", "--metacluster=utmc3"]
        self.notfoundtest(command)

    def testdelutmc4(self):
        basetime = datetime.now()
        command = ["del_metacluster", "--metacluster=utmc4"]
        self.statustest(command)
        self.wait_notification(basetime, 0)

    def testdelutmc5(self):
        basetime = datetime.now()
        command = ["del_metacluster", "--metacluster=utmc5"]
        self.statustest(command)
        self.wait_notification(basetime, 0)

    def testdelutmc6(self):
        basetime = datetime.now()
        command = ["del_metacluster", "--metacluster=utmc6"]
        self.statustest(command)
        self.wait_notification(basetime, 0)

    def testdelutmc7(self):
        basetime = datetime.now()
        command = ["del_metacluster", "--metacluster=utmc7"]
        self.statustest(command)
        self.wait_notification(basetime, 0)

    def testdelutsandbox(self):
        # Test moving machines between metaclusters
        basetime = datetime.now()
        command = ["del_metacluster", "--metacluster=sandboxmc"]
        self.statustest(command)
        self.wait_notification(basetime, 0)

    def testdelvulcan1(self):
        basetime = datetime.now()
        command = ["del_metacluster", "--metacluster=vulcan1"]
        self.statustest(command)
        self.wait_notification(basetime, 0)

    def testverifyall(self):
        command = ["show_metacluster", "--all"]
        out = self.commandtest(command)
        self.matchclean(out, "Metacluster: utmc", command)

    def testdelnotfound(self):
        command = ["del_metacluster",
                   "--metacluster=metacluster-does-not-exist"]
        self.notfoundtest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelMetaCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
