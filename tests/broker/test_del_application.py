#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013,2014,2015,2016  Contributor
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
"""Module for testing the del application command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelApplication(TestBrokerCommand):

    def test_100_del_application(self):
        path = ["resource", "host", "server1.aqd-unittest.ms.com",
                "application", "app1", "config"]
        self.check_plenary_exists(*path)
        command = ["del_application", "--application=app1",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)
        self.check_plenary_gone(*path)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelApplication)
    unittest.TextTestRunner(verbosity=2).run(suite)
