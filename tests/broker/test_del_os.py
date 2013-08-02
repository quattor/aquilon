#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2012,2013  Contributor
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
"""Module for testing the del os command."""


if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestDelOS(TestBrokerCommand):

    def testdelutos(self):
        command = ["del_os", "--archetype=utarchetype1",
                   "--osname=utos", "--osversion=1.0"]
        self.noouttest(command)

    def testverifydelos(self):
        command = "show os --osname utos --archetype=utarchetype1"
        self.notfoundtest(command.split(" "))

    def testdelinvalid(self):
        command = ["del_os", "--archetype=utarchetype1",
                   "--osname=os-does-not-exist", "--osvers=1.0"]
        self.notfoundtest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelOS)
    unittest.TextTestRunner(verbosity=2).run(suite)
