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
"""Module for testing the del_entitlement command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelEntitlement(TestBrokerCommand):

    def _test_del(self, parameters, entries):
        # Check that the entry was there previously
        command = ['search_entitlement'] + parameters
        out = self.commandtest(command)
        self.output_unordered_equals(out, entries, command, match_all=False)

        # Delete the entry
        command = ['del_entitlement'] + parameters
        self.noouttest(command)

        # Check that the entry is not there anymore
        command = ['search_entitlement'] + parameters
        out = self.commandtest(command)
        self.output_unordered_clean(out, entries, command)

    #
    # 1xx => test all working "to_" options
    #

    def test_100_del_etype_human_to_human_on_hostname(self):
        parameters = [
            '--type', 'etype_human',
            '--to_user', 'testuser1',
            '--on_hostname', 'unittest02.one-nyp.ms.com',
        ]
        entries = ['\n'.join(n) for n in [
            ('Entitlement: etype_human',
             '  To Human User: testuser1',
             '  On Host: unittest02.one-nyp.ms.com'),
        ]]
        self._test_del(parameters, entries)

    def test_100_del_etype_robot_to_robot_on_hostname(self):
        parameters = [
            '--type', 'etype_robot',
            '--to_user', 'testbot1',
            '--on_hostname', 'unittest02.one-nyp.ms.com',
        ]
        entries = ['\n'.join(n) for n in [
            ('Entitlement: etype_robot',
             '  To Robot User: testbot1',
             '  On Host: unittest02.one-nyp.ms.com'),
        ]]
        self._test_del(parameters, entries)

    def test_100_del_etype_grn_to_grn_on_hostname(self):
        parameters = [
            '--type', 'etype_grn',
            '--to_grn', 'grn:/ms/ei/aquilon/aqd',
            '--on_hostname', 'unittest02.one-nyp.ms.com',
        ]
        entries = ['\n'.join(n) for n in [
            ('Entitlement: etype_grn',
             '  To GRN: grn:/ms/ei/aquilon/aqd',
             '  On Host: unittest02.one-nyp.ms.com'),
        ]]
        self._test_del(parameters, entries)

    def test_100_del_etype_grn_to_eon_id_on_hostname(self):
        parameters = [
            '--type', 'etype_grn',
            '--to_eon_id', 3,
            '--on_hostname', 'unittest02.one-nyp.ms.com',
        ]
        entries = ['\n'.join(n) for n in [
            ('Entitlement: etype_grn',
             '  To GRN: grn:/ms/ei/aquilon/unittest',
             '  On Host: unittest02.one-nyp.ms.com'),
        ]]
        self._test_del(parameters, entries)

    #
    # 2xx => test all working "on_" options
    #

    def test_200_del_etype_all_to_human_on_cluster(self):
        parameters = [
            '--type', 'etype_all',
            '--to_user', 'testuser1',
            '--on_cluster', 'utecl1',
        ]
        entries = ['\n'.join(n) for n in [
            ('Entitlement: etype_all',
             '  To Human User: testuser1',
             '  On ESX Cluster: utecl1'),
        ]]
        self._test_del(parameters, entries)

    def test_200_del_etype_all_to_human_on_personality(self):
        parameters = [
            '--type', 'etype_all',
            '--to_user', 'testuser1',
            '--on_personality', 'compileserver',
        ]
        entries = ['\n'.join(n) for n in [
            ('Entitlement: etype_all',
             '  To Human User: testuser1',
             '  On Personality: compileserver',
             '  On Organization: ms'),
        ]]
        self._test_del(parameters, entries)

    def test_200_del_etype_all_to_human_on_personality_on_location(self):
        parameters = [
            '--type', 'etype_all',
            '--to_user', 'testuser2',
            '--on_personality', 'compileserver',
            '--on_hub', 'ny',
        ]
        entries = ['\n'.join(n) for n in [
            ('Entitlement: etype_all',
             '  To Human User: testuser2',
             '  On Personality: compileserver',
             '  On Hub: ny'),
        ]]
        self._test_del(parameters, entries)

    def test_200_del_etype_all_to_human_on_archetype(self):
        parameters = [
            '--type', 'etype_all',
            '--to_user', 'testuser1',
            '--on_archetype', 'aquilon',
            '--on_host_environment', 'dev',
        ]
        entries = ['\n'.join(n) for n in [
            ('Entitlement: etype_all',
             '  To Human User: testuser1',
             '  On Archetype: aquilon',
             '  On Host Environment: dev',
             '  On Organization: ms'),
        ]]
        self._test_del(parameters, entries)

    def test_200_del_etype_all_to_human_on_archetype_on_location(self):
        parameters = [
            '--type', 'etype_all',
            '--to_user', 'testuser2',
            '--on_archetype', 'aquilon',
            '--on_host_environment', 'dev',
            '--on_hub', 'ny',
        ]
        entries = ['\n'.join(n) for n in [
            ('Entitlement: etype_all',
             '  To Human User: testuser2',
             '  On Archetype: aquilon',
             '  On Host Environment: dev',
             '  On Hub: ny'),
        ]]
        self._test_del(parameters, entries)

    def test_200_del_etype_all_to_human_on_grn(self):
        parameters = [
            '--type', 'etype_all',
            '--to_user', 'testuser1',
            '--on_grn', 'grn:/ms/ei/aquilon/ut2',
            '--on_host_environment', 'dev',
        ]
        entries = ['\n'.join(n) for n in [
            ('Entitlement: etype_all',
             '  To Human User: testuser1',
             '  On GRN: grn:/ms/ei/aquilon/ut2',
             '  On Host Environment: dev',
             '  On Organization: ms'),
        ]]
        self._test_del(parameters, entries)

    def test_200_del_etype_all_to_human_on_grn_on_location(self):
        parameters = [
            '--type', 'etype_all',
            '--to_user', 'testuser2',
            '--on_grn', 'grn:/ms/ei/aquilon/ut2',
            '--on_host_environment', 'dev',
            '--on_hub', 'ny',
        ]
        entries = ['\n'.join(n) for n in [
            ('Entitlement: etype_all',
             '  To Human User: testuser2',
             '  On GRN: grn:/ms/ei/aquilon/ut2',
             '  On Host Environment: dev',
             '  On Hub: ny'),
        ]]
        self._test_del(parameters, entries)

    def test_200_del_etype_all_to_human_on_eon_id(self):
        parameters = [
            '--type', 'etype_all',
            '--to_user', 'testuser1',
            '--on_eon_id', 3,
            '--on_host_environment', 'dev',
        ]
        entries = ['\n'.join(n) for n in [
            ('Entitlement: etype_all',
             '  To Human User: testuser1',
             '  On GRN: grn:/ms/ei/aquilon/unittest',
             '  On Host Environment: dev',
             '  On Organization: ms'),
        ]]
        self._test_del(parameters, entries)

    def test_200_del_etype_all_to_human_on_eon_id_on_location(self):
        parameters = [
            '--type', 'etype_all',
            '--to_user', 'testuser2',
            '--on_eon_id', 3,
            '--on_host_environment', 'dev',
            '--on_hub', 'ny',
        ]
        entries = ['\n'.join(n) for n in [
            ('Entitlement: etype_all',
             '  To Human User: testuser2',
             '  On GRN: grn:/ms/ei/aquilon/unittest',
             '  On Host Environment: dev',
             '  On Hub: ny'),
        ]]
        self._test_del(parameters, entries)

    #
    # 65x => test all errors related to "on_" options
    #

    def test_650_del_on_archetype_no_host_environment(self):
        command = [
            'del_entitlement',
            '--type', 'etype_all',
            '--to_user', 'testuser3',
            '--on_archetype', 'aquilon',
        ]
        err = self.badoptiontest(command)
        self.matchoutput(err,
                         'Option or option group on_archetype can only be '
                         'used together with one of: on_host_environment.',
                         command)

    def test_650_del_on_grn_no_host_environment(self):
        command = [
            'del_entitlement',
            '--type', 'etype_all',
            '--to_user', 'testuser3',
            '--on_grn', 'grn:/ms/ei/aquilon/ut2',
        ]
        err = self.badoptiontest(command)
        self.matchoutput(err,
                         'Option or option group on_grn can only be used '
                         'together with one of: on_host_environment.',
                         command)

    def test_650_del_on_eon_id_no_host_environment(self):
        command = [
            'del_entitlement',
            '--type', 'etype_all',
            '--to_user', 'testuser3',
            '--on_eon_id', 3,
        ]
        err = self.badoptiontest(command)
        self.matchoutput(err,
                         'Option or option group on_eon_id can only be used '
                         'together with one of: on_host_environment.',
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelEntitlement)
    unittest.TextTestRunner(verbosity=2).run(suite)
