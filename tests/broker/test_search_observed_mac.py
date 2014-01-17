#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014  Contributor
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
"""Module for testing the search observed mac command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestSearchObservedMac(TestBrokerCommand):

    def testswitch(self):
        command = ["search_observed_mac",
                   "--network_device=ut01ga2s01.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "ut01ga2s01.aqd-unittest.ms.com,1,02:02:04:02:06:cb,", command)
        self.matchoutput(out, "ut01ga2s01.aqd-unittest.ms.com,2,02:02:04:02:06:cc,", command)
        self.matchclean(out, "ut01ga2s02.aqd-unittest.ms.com", command)

    def testmac(self):
        command = ["search_observed_mac", "--mac=02:02:04:02:06:cb"]
        out = self.commandtest(command)
        self.matchoutput(out, "ut01ga2s01.aqd-unittest.ms.com,1,02:02:04:02:06:cb,", command)
        self.matchclean(out, "02:02:04:02:06:cc", command)
        self.matchclean(out, "ut01ga2s02.aqd-unittest.ms.com", command)

    def testall(self):
        command = ["search_observed_mac", "--mac=02:02:04:02:06:cb",
                   "--port=1", "--network_device=ut01ga2s01.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "ut01ga2s01.aqd-unittest.ms.com,1,02:02:04:02:06:cb,", command)
        self.matchclean(out, "02:02:04:02:06:cc", command)
        self.matchclean(out, "ut01ga2s02.aqd-unittest.ms.com", command)

    def testallnegative(self):
        command = ["search_observed_mac", "--mac=02:02:04:02:06:cb",
                   "--port=2", "--network_device=ut01ga2s01.aqd-unittest.ms.com"]
        self.noouttest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSearchObservedMac)
    unittest.TextTestRunner(verbosity=2).run(suite)
