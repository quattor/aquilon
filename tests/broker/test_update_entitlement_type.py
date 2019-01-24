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
"""Module for testing the update_entitlement_type command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUpdateEntitlementType(TestBrokerCommand):

    def test_100_etype_all_disable_human(self):
        command = [
            'update_entitlement_type',
            '--type', 'etype_all',
            '--disable_to_user_type', 'human',
        ]
        self.noouttest(command)

    def test_105_show_etype_all(self):
        command = [
            'show_entitlement_type',
            '--type', 'etype_all',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('Entitlement type: etype_all',
                       '  To GRN: enabled',
                       '  To User Types: robot, superheros',
                       '  Comments: Entitlement Type to all'))
        self.output_equals(out, expected_out, command)

    def test_110_etype_all_disable_robot(self):
        command = [
            'update_entitlement_type',
            '--type', 'etype_all',
            '--disable_to_user_type', 'robot',
        ]
        self.noouttest(command)

    def test_115_show_etype_all(self):
        command = [
            'show_entitlement_type',
            '--type', 'etype_all',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('Entitlement type: etype_all',
                       '  To GRN: enabled',
                       '  To User Types: superheros',
                       '  Comments: Entitlement Type to all'))
        self.output_equals(out, expected_out, command)

    def test_120_etype_all_disable_superheros(self):
        command = [
            'update_entitlement_type',
            '--type', 'etype_all',
            '--disable_to_user_type', 'superheros',
        ]
        self.noouttest(command)

    def test_125_show_etype_all(self):
        command = [
            'show_entitlement_type',
            '--type', 'etype_all',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('Entitlement type: etype_all',
                       '  To GRN: enabled',
                       '  Comments: Entitlement Type to all'))
        self.output_equals(out, expected_out, command)

    def test_130_etype_all_disable_grn(self):
        command = [
            'update_entitlement_type',
            '--type', 'etype_all',
            '--disable_to_grn',
        ]
        self.noouttest(command)

    def test_135_show_etype_all(self):
        command = [
            'show_entitlement_type',
            '--type', 'etype_all',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('Entitlement type: etype_all',
                       '  To GRN: disabled',
                       '  Comments: Entitlement Type to all'))
        self.output_equals(out, expected_out, command)

    def test_200_etype_all_enable_grn(self):
        command = [
            'update_entitlement_type',
            '--type', 'etype_all',
            '--enable_to_grn',
        ]
        self.noouttest(command)

    def test_205_show_etype_all(self):
        command = [
            'show_entitlement_type',
            '--type', 'etype_all',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('Entitlement type: etype_all',
                       '  To GRN: enabled',
                       '  Comments: Entitlement Type to all'))
        self.output_equals(out, expected_out, command)

    def test_210_etype_all_enable_superheros(self):
        command = [
            'update_entitlement_type',
            '--type', 'etype_all',
            '--enable_to_user_type', 'superheros',
        ]
        self.noouttest(command)

    def test_215_show_etype_all(self):
        command = [
            'show_entitlement_type',
            '--type', 'etype_all',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('Entitlement type: etype_all',
                       '  To GRN: enabled',
                       '  To User Types: superheros',
                       '  Comments: Entitlement Type to all'))
        self.output_equals(out, expected_out, command)

    def test_220_etype_all_enable_robot(self):
        command = [
            'update_entitlement_type',
            '--type', 'etype_all',
            '--enable_to_user_type', 'robot',
        ]
        self.noouttest(command)

    def test_225_show_etype_all(self):
        command = [
            'show_entitlement_type',
            '--type', 'etype_all',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('Entitlement type: etype_all',
                       '  To GRN: enabled',
                       '  To User Types: robot, superheros',
                       '  Comments: Entitlement Type to all'))
        self.output_equals(out, expected_out, command)

    def test_230_etype_all_enable_human(self):
        command = [
            'update_entitlement_type',
            '--type', 'etype_all',
            '--enable_to_user_type', 'human',
        ]
        self.noouttest(command)

    def test_235_show_etype_all(self):
        command = [
            'show_entitlement_type',
            '--type', 'etype_all',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('Entitlement type: etype_all',
                       '  To GRN: enabled',
                       '  To User Types: human, robot, superheros',
                       '  Comments: Entitlement Type to all'))
        self.output_equals(out, expected_out, command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(
        TestUpdateEntitlementType)
    unittest.TextTestRunner(verbosity=2).run(suite)
