#!/usr/bin/env python2.6
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
"""Module for testing the add archetype command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddArchetype(TestBrokerCommand):

    def testaddreservedname(self):
        command = "add archetype --archetype hardware"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Archetype name hardware is reserved", command)

    def testaddexisting(self):
        command = "add archetype --archetype aquilon"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Archetype aquilon already exists", command)

    def testaddbadname(self):
        command = "add archetype --archetype oops@!"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Archetype name 'oops@!' is not valid", command)

    def testaddbadcluster(self):
        command = ["add_archetype", "--archetype", "bad-cluster",
                   "--cluster_type", "bad-cluster-type"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Unknown cluster type 'bad-cluster-type'. The valid "
                         "values are: compute, esx, meta, storage.",
                         command)

    def testaddgridarchetype(self):
        command = ["add_archetype", "--archetype=gridcluster", "--cluster=compute",
                   "--compilable", "--description=Grid"]
        self.noouttest(command)
        command = "show archetype --archetype gridcluster"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Cluster Archetype: gridcluster", command)
        self.matchoutput(out, "compilable", command)

    def testaddhaarchetype(self):
        command = ["add_archetype", "--archetype=hacluster",
                   "--cluster=compute", "--compilable",
                   "--description=High Availability"]
        self.noouttest(command)
        command = "show archetype --archetype hacluster"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Cluster Archetype: hacluster", command)
        self.matchoutput(out, "compilable", command)

    def testaddutarchetype1(self):
        command = "add archetype --archetype utarchetype1"
        self.noouttest(command.split(" "))

    def testaddutarchetype2(self):
        command = "add archetype --archetype utarchetype2"
        self.noouttest(command.split(" "))

    def testaddutarchetype3(self):
        command = "add archetype --archetype utarchetype3"
        self.noouttest(command.split(" "))

    def testverifyutarchetype(self):
        command = "show archetype --archetype utarchetype1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Archetype: utarchetype1", command)
        self.matchclean(out, "compilable", command)
        self.matchclean(out, "[", command)
        self.matchclean(out, "Required Service", command)

    def testverifyutarchetypeall(self):
        command = "show archetype --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Archetype: utarchetype1", command)
        self.matchoutput(out, "Archetype: utarchetype2", command)
        self.matchoutput(out, "Archetype: aquilon [compilable]", command)

    def testnotfoundarchetype(self):
        command = "show archetype --archetype archetype-does-not-exist"
        self.notfoundtest(command.split(" "))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddArchetype)
    unittest.TextTestRunner(verbosity=2).run(suite)
