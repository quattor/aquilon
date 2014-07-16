#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014  Contributor
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
"""Module for testing the del user command."""

import pwd
import os

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestDelUser(TestBrokerCommand):
    def test_100_del_current_user(self):
        pwrec = pwd.getpwuid(os.getuid())
        self.noouttest(["del_user", "--username", pwrec[0]])

    def test_105_verify_gone(self):
        pwrec = pwd.getpwuid(os.getuid())
        command = ["show_user", "--username", pwrec[0]]
        out = self.notfoundtest(command)
        self.matchoutput(out, "User %s not found." % pwrec[0], command)

    def test_110_del_current_user_again(self):
        pwrec = pwd.getpwuid(os.getuid())
        command = ["del_user", "--username", pwrec[0]]
        out = self.notfoundtest(command)
        self.matchoutput(out, "User %s not found." % pwrec[0], command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelUser)
    unittest.TextTestRunner(verbosity=2).run(suite)
