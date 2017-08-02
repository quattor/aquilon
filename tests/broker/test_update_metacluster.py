#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2012,2013,2014,2015,2016,2017  Contributor
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
"""Module for testing the update metacluster command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand
from personalitytest import PersonalityTestMixin


class TestUpdateMetaCluster(TestBrokerCommand, PersonalityTestMixin):

    def test_000_add_personalities(self):
        self.create_personality("metacluster", "metacluster-test",
                                grn="grn:/ms/ei/aquilon/aqd")

    def test_100_updatenoop(self):
        default_max = self.config.getint("archetype_metacluster",
                                         "max_members_default")
        self.noouttest(["update_metacluster", "--metacluster=utmc1",
                        "--max_members=%s" % default_max, "--justification", "tcm=123"])

    def test_100_verifynoop(self):
        command = "show metacluster --metacluster utmc1"
        out = self.commandtest(command.split(" "))
        default_max = self.config.getint("archetype_metacluster",
                                         "max_members_default")
        self.matchoutput(out, "MetaCluster: utmc1", command)
        self.matchoutput(out, "Max members: %s" % default_max, command)
        self.matchclean(out, "Comments", command)

    def test_100_updateutmc2(self):
        command = ["update_metacluster", "--metacluster=utmc2",
                   "--max_members=98",
                   "--comments", "New metacluster comments"]
        self.noouttest(command)

    def test_100_verifyutmc2(self):
        command = "show metacluster --metacluster utmc2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "MetaCluster: utmc2", command)
        self.matchoutput(out, "Max members: 98", command)
        self.matchoutput(out, "Comments: New metacluster comments",
                         command)

    def test_100_failmetaclustermissing(self):
        command = "update metacluster --metacluster metacluster-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out,
                         "Metacluster metacluster-does-not-exist not found",
                         command)

    def test_100_failreducemaxmembers(self):
        command = ["update_metacluster", "--metacluster=utmc1",
                   "--max_members=1", "--justification", "tcm=123"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Metacluster utmc1 has 3 clusters bound, "
                         "which exceeds the requested limit of 1.",
                         command)

    # FIXME: Need tests for plenary templates

    def test_100_updatelocation(self):
        # moving cluster from bu: ut to city ny, a parent of it.
        command = ["update_metacluster", "--metacluster", "utmc1",
                   "--city", "ny", "--justification", "tcm=123"]
        self.noouttest(command)

        command = ["show", "metacluster", "--metacluster", "utmc1"]
        out = self.commandtest(command)
        self.matchoutput(out, "City: ny", command)

        command = ["cat", "--metacluster", "utmc1", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         '"system/metacluster/sysloc/city" = "ny";',
                         command)
        self.matchclean(out, "system/metacluster/sysloc/building", command)
        self.matchoutput(out,
                         '"system/metacluster/sysloc/location" = null',
                         command)

        # reverting this move
        command = ["update_metacluster", "--metacluster", "utmc1",
                   "--fix_location"]
        self.noouttest(command)

        command = ["show", "metacluster", "--metacluster", "utmc1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Building: ut", command)

    def test_100_updatepersonality(self):
        # Change metacluster personality and revert it.
        command = ["update_metacluster", "--metacluster", "utmc1",
                   "--personality", "metacluster-test", "--justification", "tcm=123"]
        self.noouttest(command)

        command = ["show", "metacluster", "--metacluster", "utmc1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Personality: metacluster-test", command)

        command = ["update_metacluster", "--metacluster", "utmc1",
                   "--personality", "metacluster"]
        self.noouttest(command)

        command = ["show", "metacluster", "--metacluster", "utmc1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Personality: metacluster", command)

    def test_100_failupdatelocation(self):
        command = ["update_metacluster", "--metacluster", "utmc1",
                   "--building", "cards", "--justification", "tcm=123"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "ESX Cluster utecl1 has location Building ut.",
                         command)
        self.matchoutput(out, "ESX Cluster utecl2 has location Building ut.",
                         command)

    def test_800_cleanup(self):
        self.drop_personality("metacluster", "metacluster-test")

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateMetaCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
