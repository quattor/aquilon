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
"""Module for testing the del archetype command."""

if __name__ == "__main__":
    from broker import utils
    utils.import_depends()

import unittest2 as unittest
from broker.brokertest import TestBrokerCommand


class TestDelArchetype(TestBrokerCommand):

    def testdelutarchetype1(self):
        command = ["del_archetype", "--archetype=utarchetype1"]
        self.noouttest(command)

    def testdelutarchetype2(self):
        command = ["del_archetype", "--archetype=utarchetype2"]
        self.noouttest(command)

    def testdelutarchetype3(self):
        command = ["del_archetype", "--archetype=utarchetype3"]
        self.noouttest(command)

    def testverifydelutarchetype1(self):
        command = ["show_archetype", "--archetype=utarchetype1"]
        self.notfoundtest(command)

    def testverifydelutarchetype2(self):
        command = ["show_archetype", "--archetype=utarchetype2"]
        self.notfoundtest(command)

    def testverifydelutarchetype3(self):
        command = ["show_archetype", "--archetype=utarchetype3"]
        self.notfoundtest(command)

    def testverifyall(self):
        command = ["show_archetype", "--all"]
        out = self.commandtest(command)
        self.matchclean(out, "Archetype: utarchetype", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelArchetype)
    unittest.TextTestRunner(verbosity=2).run(suite)
