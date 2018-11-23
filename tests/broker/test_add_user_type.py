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
"""Module for testing the add_user_type command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddUserType(TestBrokerCommand):

    def test_100_add_superheros(self):
        command = [
            'add_user_type',
            '--type', 'superheros',
            '--comments', 'Super Heros',
        ]
        self.noouttest(command)

    def test_105_show_superheros(self):
        command = [
            'show_user_type',
            '--type', 'superheros',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('User type: superheros',
                       '  Comments: Super Heros'))
        self.output_equals(out, expected_out, command)

    def test_110_add_robot(self):
        command = [
            'add_user_type',
            '--type', 'robot',
            '--comments', 'H2G2',
        ]
        self.noouttest(command)

    def test_115_show_robot(self):
        command = [
            'show_user_type',
            '--type', 'robot',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('User type: robot',
                       '  Comments: H2G2'))
        self.output_equals(out, expected_out, command)

    def test_200_update_robot(self):
        command = [
            'update_user_type',
            '--type', 'robot',
            '--comments', "It's me Nono, small robot, you know!",
        ]
        self.noouttest(command)

    def test_205_show_robot(self):
        command = [
            'show_user_type',
            '--type', 'robot',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('User type: robot',
                       "  Comments: It's me Nono, small robot, you know!"))
        self.output_equals(out, expected_out, command)

    def test_300_show_all(self):
        command = [
            'show_user_type',
            '--all',
        ]
        out = self.commandtest(command)
        self.matchoutput(out, 'User type: human', command)
        self.matchoutput(out, 'User type: robot', command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddUserType)
    unittest.TextTestRunner(verbosity=2).run(suite)
