#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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
"""Module for testing constraints in commands involving clusters."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestClusterConstraints(TestBrokerCommand):

    def testdelclusterwithmachines(self):
        command = "del esx cluster --cluster utecl1"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "ESX Cluster utecl1 is still in use by virtual "
                         "machines", command)

    def testverifydelclusterwithmachines(self):
        command = ["show_esx_cluster", "--cluster=utecl1"]
        out = self.commandtest(command)
        self.matchoutput(out, "ESX Cluster: utecl1", command)

    def testupdatevmhostmemory(self):
        command = ["update", "machine", "--machine", "np13s03p13",
                   "--memory", 8192]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "ESX Cluster npecl12 is over capacity regarding memory",
                         command)

    def testupdatevmmeory(self):
        command = ["update", "machine", "--machine", "evm110",
                   "--memory", 81920]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "ESX Cluster npecl12 is over capacity regarding memory",
                         command)

    def testunbindmachine(self):
        command = ["uncluster", "--hostname", "evh87.one-nyp.ms.com",
                   "--cluster", "npecl12", "--personality", "generic"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "ESX Cluster npecl12 is over capacity regarding memory",
                         command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestClusterConstraints)
    unittest.TextTestRunner(verbosity=2).run(suite)
