#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2013  Contributor
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
"""Module for testing the del chassis command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelChassis(TestBrokerCommand):

    def testdelut3c5(self):
        self.dsdb_expect_delete(self.net["unknown0"].usable[6])
        command = "del chassis --chassis ut3c5.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))
        self.dsdb_verify()

    def testverifydelut3c5(self):
        command = "show chassis --chassis ut3c5.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelut3c1(self):
        command = "del chassis --chassis ut3c1.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelut3c1(self):
        command = "show chassis --chassis ut3c1.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelut9chassis(self):
        for i in range(1, 6):
            self.dsdb_expect_delete(self.net["unknown10"].usable[i])
            command = "del chassis --chassis ut9c%d.aqd-unittest.ms.com" % i
            self.noouttest(command.split(" "))
        self.dsdb_verify()

    def testverifydelut9chassis(self):
        for i in range(1, 6):
            command = "show chassis --chassis ut9c%d.aqd-unittest.ms.com" % i
            self.notfoundtest(command.split(" "))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelChassis)
    unittest.TextTestRunner(verbosity=2).run(suite)
