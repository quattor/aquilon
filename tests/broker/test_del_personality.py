#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013  Contributor
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
"""Module for testing the del personality command."""

import unittest
import os.path

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelPersonality(TestBrokerCommand):

    def testdelutpersonality(self):
        command = ["del_personality", "--personality=utpersonality/dev",
                   "--archetype=aquilon"]
        self.noouttest(command)

    def testverifyplenarydir(self):
        dir = os.path.join(self.config.get("broker", "plenarydir"),
                           "aquilon", "personality", "utpersonality")
        self.failIf(os.path.exists(dir),
                    "Plenary directory '%s' still exists" % dir)

    def testdeleaipersonality(self):
        command = ["del_personality", "--personality=eaitools",
                   "--archetype=aquilon"]
        self.noouttest(command)

    def testverifydelutpersonality(self):
        command = ["show_personality", "--personality=utpersonality",
                   "--archetype=aquilon"]
        self.notfoundtest(command)

    def testdelwindowsdesktop(self):
        command = "del personality --personality desktop --archetype windows"
        self.noouttest(command.split(" "))

    def testverifydelwindowsdesktop(self):
        command = "show personality --personality desktop --archetype windows"
        self.notfoundtest(command.split(" "))

    def testdelbadaquilonpersonality(self):
        command = ["del_personality", "--personality=badpersonality",
                   "--archetype=aquilon"]
        self.noouttest(command)

    def testverifydelbadaquilonpersonality(self):
        command = ["show_personality", "--personality=badpersonality",
                   "--archetype=aquilon"]
        self.notfoundtest(command)

    def testdelbadaquilonpersonality2(self):
        command = ["del_personality", "--personality=badpersonality2",
                   "--archetype=aquilon"]
        self.noouttest(command)

    def testverifydelbadaquilonpersonality2(self):
        command = ["show_personality", "--personality=badpersonality2",
                   "--archetype=aquilon"]
        self.notfoundtest(command)

    def testdelesxserver(self):
        command = "del personality --personality esx_server --archetype vmhost"
        self.noouttest(command.split(" "))

    def testdelv1personalities(self):
        command = ["del_personality",
                   "--personality=vulcan-1g-desktop-prod", "--archetype=vmhost"]
        self.noouttest(command)
        command = ["del_personality",
                   "--personality=metacluster", "--archetype=metacluster"]
        self.noouttest(command)

    def testdelv2personalities(self):
        command = ["del_personality",
                   "--personality=vulcan2-10g-test", "--archetype=vmhost"]
        self.noouttest(command)
        command = ["del_personality",
                   "--personality=vulcan2-10g-test", "--archetype=esx_cluster"]
        self.noouttest(command)
        command = ["del_personality",
                   "--personality=vulcan2-test", "--archetype=metacluster"]
        self.noouttest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelPersonality)
    unittest.TextTestRunner(verbosity=2).run(suite)
