#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2013  Contributor
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
"""Module for testing constraints in commands involving personality."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestPersonalityConstraints(TestBrokerCommand):

    def testdelpersonalitywithhost(self):
        command = "del personality --personality inventory --archetype aquilon"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "is still in use and cannot be deleted", command)

    def testdelpersonalitywithcluster(self):
        command = ["del_personality", "--personality", "vulcan-1g-desktop-prod",
                   "--archetype", "esx_cluster"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "is still in use and cannot be deleted", command)

    def testverifydelpersonalitywithhostfailed(self):
        command = ["show_personality", "--personality=inventory",
                   "--archetype=aquilon"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Personality: inventory Archetype: aquilon",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(
        TestPersonalityConstraints)
    unittest.TextTestRunner(verbosity=2).run(suite)
