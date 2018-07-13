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
"""Module for testing the del_entitlement_type command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelEntitlementType(TestBrokerCommand):

    def test_100_del_etype_human(self):
        command = [
            'del_entitlement_type',
            '--type', 'etype_human',
        ]
        self.noouttest(command)

    def test_105_verify_etype_human(self):
        command = [
            'show_entitlement_type',
            '--type', 'etype_human',
        ]
        self.notfoundtest(command)

    def test_200_del_nonexistant(self):
        command = [
            'del_entitlement_type',
            '--type', 'etype_does_not_exist',
        ]
        out = self.notfoundtest(command)
        self.matchoutput(
            out, 'EntitlementType etype_does_not_exist not found', command)

    def test_300_show_all(self):
        command = [
            'show_entitlement_type',
            '--all',
        ]
        out = self.commandtest(command)
        self.matchoutput(out, 'etype_all', command)
        self.matchoutput(out, 'etype_robot', command)
        self.matchoutput(out, 'etype_grn', command)
        self.matchclean(out, 'etype_human', command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelEntitlementType)
    unittest.TextTestRunner(verbosity=2).run(suite)
