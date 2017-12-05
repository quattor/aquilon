#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2017  Contributor
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
"""Module for testing the change management logger."""

import json
import unittest
import os

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestCMLogger(TestBrokerCommand):

    def test_100_logger_exist(self):
        cmlogfile = self.config.get("broker", "cmlogfile")
        self.assertTrue(os.path.isfile(cmlogfile))

    def test_110_logger_populate(self):
        command = ["add", "domain", "--domain", "testcmlogger",
                   "--reason", "Test logger"]
        self.justificationmissingtest_warn(command)

    def test_120_logger_content(self):
        cmlogfile = self.config.get("broker", "cmlogfile")
        last_entry = json.loads(self.tail_file(cmlogfile))
        self.assertEqual(last_entry["reason"], "Test logger")
        self.assertEqual(last_entry["Status"], "Permitted")
        self.assertEqual(last_entry["Reason"], "No justification found, please "
                                               "supply a TCM or SN ticket. Continuing "
                                               "with execution; however in the future "
                                               "this operation will fail.")
        self.assertEqual(last_entry["command"], "add_domain")
        self.assertEqual(last_entry["disable_edm"], "Yes")
        self.assertEqual(last_entry["mode"], "warn")


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStatus)
    unittest.TextTestRunner(verbosity=2).run(suite)