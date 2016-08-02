#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014,2015,2016  Contributor
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

    def test_100_add_gridcluster(self):
        command = ["add_archetype", "--archetype=gridcluster", "--cluster=compute",
                   "--compilable", "--description=Grid"]
        self.noouttest(command)

    def test_105_show_gridcluster(self):
        command = "show archetype --archetype gridcluster"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Cluster Archetype: gridcluster", command)
        self.matchoutput(out, "compilable", command)

    def test_105_show_gridcluster_proto(self):
        command = ["show_archetype", "--archetype", "gridcluster",
                   "--format", "proto"]
        arch = self.protobuftest(command, expect=1)[0]
        self.assertEqual(arch.name, "gridcluster")
        self.assertEqual(arch.compileable, True)
        self.assertEqual(arch.cluster_type, "compute")

    def test_110_add_hacluster(self):
        command = ["add_archetype", "--archetype=hacluster",
                   "--cluster=compute", "--compilable",
                   "--description=High Availability"]
        self.noouttest(command)

    def test_115_show_hacluster(self):
        command = "show archetype --archetype hacluster"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Cluster Archetype: hacluster", command)
        self.matchoutput(out, "compilable", command)

    def test_120_add_utarchetype1(self):
        command = "add archetype --archetype utarchetype1"
        self.noouttest(command.split(" "))

    def test_120_add_utarchetype2(self):
        command = ["add_archetype", "--archetype", "utarchetype2",
                   "--comments", "Some arch comments"]
        self.noouttest(command)

    def test_120_add_utarchetype3(self):
        command = "add archetype --archetype utarchetype3"
        self.noouttest(command.split(" "))

    def test_125_show_utarchetype1(self):
        command = "show archetype --archetype utarchetype1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Archetype: utarchetype1", command)
        self.matchclean(out, "compilable", command)
        self.matchclean(out, "[", command)
        self.matchclean(out, "Required Service", command)

    def test_125_show_utarchetype2(self):
        command = "show archetype --archetype utarchetype2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Archetype: utarchetype2", command)
        self.matchoutput(out, "Some arch comments", command)
        self.matchclean(out, "compilable", command)
        self.matchclean(out, "[", command)
        self.matchclean(out, "Required Service", command)

    def test_130_add_utappliance(self):
        command = "add archetype --archetype utappliance --nocompilable"
        self.noouttest(command.split(" "))

    def test_135_show_utappliance_proto(self):
        command = ["show_archetype", "--archetype", "utappliance",
                   "--format", "proto"]
        arch = self.protobuftest(command, expect=1)[0]
        self.assertEqual(arch.name, "utappliance")
        self.assertEqual(arch.compileable, False)

    def test_200_add_reserved_name(self):
        command = "add archetype --archetype hardware"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Archetype name hardware is reserved.", command)

    def test_200_add_existing(self):
        command = "add archetype --archetype aquilon"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Archetype aquilon already exists.", command)

    def test_200_add_bad_name(self):
        command = "add archetype --archetype oops@!"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "'oops@!' is not a valid value for --archetype.",
                         command)

    def test_200_add_bad_cluster(self):
        command = ["add_archetype", "--archetype", "bad-cluster",
                   "--cluster_type", "bad-cluster-type"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Unknown cluster type 'bad-cluster-type'. The valid "
                         "values are: compute, esx, meta, storage.",
                         command)

    def test_200_show_nonexistant(self):
        command = "show archetype --archetype archetype-does-not-exist"
        self.notfoundtest(command.split(" "))

    def test_300_verify_all(self):
        command = "show archetype --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Archetype: utarchetype1", command)
        self.matchoutput(out, "Archetype: utarchetype2", command)
        self.matchoutput(out, "Archetype: aquilon [compilable]", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddArchetype)
    unittest.TextTestRunner(verbosity=2).run(suite)
