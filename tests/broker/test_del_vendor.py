#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2013  Contributor
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
"""Module for testing the del vendor command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestDelVendor(TestBrokerCommand):

    def testdelinvalidvendor(self):
        command = ["del_vendor", "--vendor=vendor-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Vendor vendor-does-not-exist not found",
                         command)

    def testdelutvendor(self):
        command = ["del_vendor", "--vendor=utvendor"]
        self.noouttest(command)

    def testverifydelutvendor(self):
        command = ["show_vendor", "--vendor=utvendor"]
        self.notfoundtest(command)

    def testverifyall(self):
        command = ["show_vendor", "--all"]
        out = self.commandtest(command)
        self.matchclean(out, "Vendor: utvendor", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelVendor)
    unittest.TextTestRunner(verbosity=2).run(suite)
