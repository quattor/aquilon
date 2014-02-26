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

    def test_100_verify_clean(self):
        # Start clean
        command = "show archetype --archetype utarchetype1"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out, r"Archetype: utarchetype1\s*$", command)
        self.matchclean(out, "Comments", command)

    def test_101_make_compilable(self):
        self.noouttest(["update_archetype", "--archetype=utarchetype1",
                        "--compilable"])

    def test_101_set_comments(self):
        self.noouttest(["update_archetype", "--archetype=utarchetype1",
                        "--comments", "Other arch comments"])

    def test_105_verify_compilable(self):
        command = "show archetype --archetype utarchetype1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Archetype: utarchetype1 [compilable]", command)
        self.matchoutput(out, "Comments: Other arch comments", command)

    def test_110_reset_compilable(self):
        self.noouttest(["update_archetype", "--archetype=utarchetype1",
                        "--nocompilable"])

    def test_110_reset_comments(self):
        self.noouttest(["update_archetype", "--archetype=utarchetype1",
                        "--comments", ""])

    def test_115_verify_updates(self):
        command = "show archetype --archetype utarchetype1"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out, r"Archetype: utarchetype1\s*$", command)
        self.matchclean(out, "Comments", command)

    def test_120_verify_clean(self):
        command = "show archetype --archetype utarchetype2"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out, r"Host Archetype: utarchetype2\s*$", command)
        self.matchoutput(out, "Comments: Some arch comments", command)

    def test_121_convert_to_cluster(self):
        self.noouttest(["update_archetype", "--archetype=utarchetype2",
                        "--cluster_type=compute"])

    def test_125_verify_cluster(self):
        command = "show archetype --archetype utarchetype2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Cluster Archetype: utarchetype2", command)

    def test_130_convert_to_host(self):
        self.noouttest(["update_archetype", "--archetype=utarchetype2",
                        "--cluster_type="])

    def test_135_verify_nocluster(self):
        command = "show archetype --archetype utarchetype2"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out, r"Host Archetype: utarchetype2\s*$", command)

    def test_200_convert_to_cluster_fail(self):
        command = ["update_archetype", "--archetype=aquilon",
                   "--cluster_type=compute"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Archetype aquilon is currently in use",
                         command)

    def test_200_convert_to_host_fail(self):
        command = ["update_archetype", "--archetype=esx_cluster",
                   "--cluster_type="]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Archetype esx_cluster is currently in use",
                         command)

    def test_200_wrong_cluster_type(self):
        command = ["update_archetype", "--archetype=esx_cluster",
                   "--cluster_type=no-such-cluster-type"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Unknown cluster type 'no-such-cluster-type'. "
                         "The valid values are: compute, esx, meta, storage.",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateArchetype)
    unittest.TextTestRunner(verbosity=2).run(suite)
