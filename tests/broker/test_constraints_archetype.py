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
"""Module for testing constraints in commands involving archetype."""

import unittest

if __name__ == "__main__":
    from broker import utils
    utils.import_depends()

from broker.brokertest import TestBrokerCommand


class TestArchetypeConstraints(TestBrokerCommand):

    def testdelarchetypewithpersonality(self):
        command = "del archetype --archetype aquilon"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Archetype aquilon is still in use by "
                         "personality aquilon/badpersonality and "
                         "cannot be deleted.",
                         command)

    def testverifydelarchetypewithmodel(self):
        command = ["show_archetype", "--archetype=aquilon"]
        out = self.commandtest(command)
        self.matchoutput(out, "Archetype: aquilon", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(
        TestArchetypeConstraints)
    unittest.TextTestRunner(verbosity=2).run(suite)
