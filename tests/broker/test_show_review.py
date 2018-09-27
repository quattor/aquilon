#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2018  Contributor
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
"""Module for testing the show review command."""


import unittest


if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestShowReview(TestBrokerCommand):

    def test_help_succeeds(self):
        command = ["show_review", "--help"]
        self.successtest(command)

    def test_show_help_if_no_arguments(self):
        # Test against regression for AQUILON-4235.
        command = "show_review"
        help_command = ["show_review", "--help"]
        help_output = self.commandtest(help_command)
        p, out, err = self.runcommand(command)
        # Does stderr contain output from --help?
        self.assertIn(help_output, err)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestShowReview)
    unittest.TextTestRunner(verbosity=2).run(suite)
