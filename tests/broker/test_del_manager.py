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
"""Module for testing the del manager command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelManager(TestBrokerCommand):

    def testdelunittest00r(self):
        self.dsdb_expect_delete(self.net["unknown0"].usable[4])
        command = "del manager --manager unittest00r.one-nyp.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        self.dsdb_verify()

    def testverifydelunittest00r(self):
        command = "show manager --manager unittest00r.one-nyp.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelunittest02rsa(self):
        self.dsdb_expect_delete(self.net["unknown0"].usable[9])
        command = "del manager --manager unittest02rsa.one-nyp.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        self.dsdb_verify()

    def testverifydelunittest02rsa(self):
        command = "show manager --manager unittest02rsa.one-nyp.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelunittest12r(self):
        self.dsdb_expect_delete(self.net["unknown0"].usable[8])
        command = "del manager --manager unittest12r.aqd-unittest.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        self.dsdb_verify()

    def testverifydelunittest12r(self):
        command = "show manager --manager unittest12r.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelManager)
    unittest.TextTestRunner(verbosity=2).run(suite)
