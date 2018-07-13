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
"""Module for testing the add_entitlement_type command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddEntitlementType(TestBrokerCommand):

    def test_100_add_etype_all(self):
        command = [
            'add_entitlement_type',
            '--type', 'etype_all',
            '--enable_to_user_type', 'human',
            '--enable_to_user_type', 'superheros',
            '--enable_to_user_type', 'robot',
            '--enable_to_grn',
            '--comments', "Entitlement Type to all",
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
                       '  To User Types: human, robot, superheros',
                       '  Comments: Entitlement Type to all'))
        self.output_equals(out, expected_out, command)

    def test_110_add_etype_human(self):
        command = [
            'add_entitlement_type',
            '--type', 'etype_human',
            '--enable_to_user_type', 'human',
            '--comments', "Entitlement Type to human",
        ]
        self.noouttest(command)

    def test_115_show_etype_human(self):
        command = [
            'show_entitlement_type',
            '--type', 'etype_human',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('Entitlement type: etype_human',
                       '  To GRN: disabled',
                       '  To User Types: human',
                       '  Comments: Entitlement Type to human'))
        self.output_equals(out, expected_out, command)

    def test_120_add_etype_robot(self):
        command = [
            'add_entitlement_type',
            '--type', 'etype_robot',
            '--enable_to_user_type', 'robot',
            '--comments', "Entitlement Type to robot",
        ]
        self.noouttest(command)

    def test_125_show_etype_robot(self):
        command = [
            'show_entitlement_type',
            '--type', 'etype_robot',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('Entitlement type: etype_robot',
                       '  To GRN: disabled',
                       '  To User Types: robot',
                       '  Comments: Entitlement Type to robot'))
        self.output_equals(out, expected_out, command)

    def test_130_add_etype_grn(self):
        command = [
            'add_entitlement_type',
            '--type', 'etype_grn',
            '--enable_to_grn',
            '--comments', "Entitlement Type to GRN",
        ]
        self.noouttest(command)

    def test_135_show_etype_grn(self):
        command = [
            'show_entitlement_type',
            '--type', 'etype_grn',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('Entitlement type: etype_grn',
                       '  To GRN: enabled',
                       '  Comments: Entitlement Type to GRN'))
        self.output_equals(out, expected_out, command)

    def test_200_show_all(self):
        command = [
            'show_entitlement_type',
            '--all',
        ]
        out = self.commandtest(command)
        self.matchoutput(out, 'etype_all', command)
        self.matchoutput(out, 'etype_robot', command)
        self.matchoutput(out, 'etype_grn', command)
        self.matchoutput(out, 'etype_human', command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddEntitlementType)
    unittest.TextTestRunner(verbosity=2).run(suite)
