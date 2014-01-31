#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013,2014  Contributor
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
"""Module for testing constraints in commands involving machine."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestMachineConstraints(TestBrokerCommand):

    def testdelmachinewithhost(self):
        command = "del machine --machine ut3c5n10"
        self.badrequesttest(command.split(" "))

    def testverifydelmachinewithhostfailed(self):
        command = "show machine --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: ut3c5n10", command)
        self.matchoutput(out, "Model Type: blade", command)

    # Expected to fail without the --all flag...
    def testdelalldisks(self):
        command = "del disk --machine ut3c5n10"
        self.badrequesttest(command.split(" "))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMachineConstraints)
    unittest.TextTestRunner(verbosity=2).run(suite)
