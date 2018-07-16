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
"""Module for testing the del_user_type command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelUserType(TestBrokerCommand):

    def test_100_del_superheros(self):
        command = [
            'del_user_type',
            '--type', 'superheros',
        ]
        self.noouttest(command)

    def test_105_verify_superheros(self):
        command = [
            'show_user_type',
            '--type', 'superheros',
        ]
        self.notfoundtest(command)

    def test_200_del_nonexistant(self):
        command = [
            'del_user_type',
            '--type', 'user_type_does_not_exist',
        ]
        out = self.notfoundtest(command)
        self.matchoutput(
            out, 'UserType user_type_does_not_exist not found', command)

    def test_250_del_in_use(self):
        command = [
            'del_user_type',
            '--type', 'human',
        ]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         'User type human is still in use by '
                         'at least one user.', command)

    def test_300_show_all(self):
        command = [
            'show_user_type',
            '--all',
        ]
        out = self.commandtest(command)
        self.matchoutput(out, 'User type: human', command)
        self.matchoutput(out, 'User type: robot', command)
        self.matchclean(out, 'User type: superheros', command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelUserType)
    unittest.TextTestRunner(verbosity=2).run(suite)
