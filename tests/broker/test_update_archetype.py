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
"""Module for testing the update archetype command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestUpdateArchetype(TestBrokerCommand):

    def testupdatecompilable(self):
        # Start clean
        command = "show archetype --archetype utarchetype1"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out, "Archetype: utarchetype1\s*$", command)

        # Set the flag
        self.noouttest(["update_archetype", "--archetype=utarchetype1",
                        "--compilable"])

        # Check the flag
        command = "show archetype --archetype utarchetype1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Archetype: utarchetype1 [compilable]", command)

        # Unset the flag
        self.noouttest(["update_archetype", "--archetype=utarchetype1",
                        "--nocompilable"])

        # End clean
        command = "show archetype --archetype utarchetype1"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out, "Archetype: utarchetype1\s*$", command)

    def testupdate_to_cluster(self):
        # Start clean
        command = "show archetype --archetype utarchetype2"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out, "Host Archetype: utarchetype2\s*$", command)

        # Set the flag
        out = self.successtest(["update_archetype",
                                "--archetype=utarchetype2",
                                "--cluster=compute"])

        # Check the flag
        command = "show archetype --archetype utarchetype2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Cluster Archetype: utarchetype2", command)

        # Unset the flag
        self.noouttest(["update_archetype", "--archetype=utarchetype2",
                        "--cluster="])

        # End clean
        command = "show archetype --archetype utarchetype2"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out, "Host Archetype: utarchetype2\s*$", command)

    def testfailupdate_to_cluster(self):
        # Set the flag
        command = ["update_archetype", "--archetype=aquilon",
                   "--cluster=compute"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The aquilon archetype is currently in use",
                         command)

        command = ["update_archetype", "--archetype=esx_cluster",
                   "--cluster="]
        out = self.badrequesttest(command)

        self.matchoutput(out, "The esx_cluster archetype is currently in use",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateArchetype)
    unittest.TextTestRunner(verbosity=2).run(suite)
