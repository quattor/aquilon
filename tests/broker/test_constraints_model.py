#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2015  Contributor
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
"""Module for testing constraints in commands involving models."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestModelConstraints(TestBrokerCommand):

    def test_100_del_machine_model(self):
        command = ["del_model", "--model", "hs21-8853", "--vendor", "ibm"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Model ibm/hs21-8853 is still in use and "
                         "cannot be deleted.", command)

    def test_120_del_nic_model(self):
        command = ["del", "model", "--model", "default", "--vendor", "utvirt"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Model utvirt/default is still in use and "
                         "cannot be deleted.", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(
        TestModelConstraints)
    unittest.TextTestRunner(verbosity=2).run(suite)
