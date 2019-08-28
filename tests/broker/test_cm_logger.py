# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2017,2019  Contributor
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
import os
import re
import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from utils import MockHub

from brokertest import TestBrokerCommand


class TestCMLogger(TestBrokerCommand):

    def extract_first_occurrence_or_fail(self, command, pattern):
        out = self.commandtest(command)
        for line in out.splitlines():
            found = re.findall(pattern, line)
            if found:
                return found[0]
        else:
            self.fail('No match for pattern "{}" found in:\n{}\n'.format(
                pattern, out))

    def test_100_logger_exist(self):
        cmlogfile = self.config.get("broker", "cmlogfile")
        self.assertTrue(os.path.isfile(cmlogfile))

    def test_110_logger_populate(self):
        command = ["add", "domain", "--domain", "testcmlogger",
                   "--reason", "Test logger"]
        self.justificationmissingtest_warn(command)

    def test_120_logger_content(self):
        cmlogfile = self.config.get('broker', 'cmlogfile')
        last_entry = json.loads(self.tail_file(cmlogfile))
        self.assertEqual(last_entry['reason'], 'Test logger')
        self.assertTrue(last_entry['request_id'])
        self.assertEqual(last_entry['Status'], 'Permitted')
        self.assertEqual(last_entry['Reason'],
                         'No justification found, please '
                         'supply a TCM or SN ticket. Continuing '
                         'with execution; however in the future '
                         'this operation will fail.')
        self.assertEqual(last_entry['command'], 'add_domain')
        self.assertEqual(last_entry['disable_edm'], 'Yes')
        self.assertEqual(last_entry['mode'], 'warn')
        # There should be no impacted EON IDs at this point.
        self.assertEqual(last_entry['impacted_eonids'], [])

    def test_200_eon_ids_logged(self):
        mh = MockHub(self)
        mh.add_host()
        cmlogfile = self.config.get('broker', 'cmlogfile')
        last_entry = json.loads(self.tail_file(cmlogfile))
        command = ['show_grn', '--grn', mh.grn]
        eon_id = int(self.extract_first_occurrence_or_fail(
            command, r'EON ID:[\s]*([\d]+)'))
        self.assertEqual(last_entry['impacted_eonids'], [eon_id])
        mh.delete()


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCMLogger)
    # noinspection PyUnresolvedReferences
    unittest.TextTestRunner(verbosity=2).run(suite)
