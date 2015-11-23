#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014,2015  Contributor
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
"""Module for testing the add metacluster command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand
from personalitytest import PersonalityTestMixin


class TestAddMetaCluster(PersonalityTestMixin, TestBrokerCommand):

    def test_000_add_personality(self):
        # The broker currently assumes this personality to exist
        self.create_personality("metacluster", "metacluster",
                                grn="grn:/ms/ei/aquilon/aqd")

        self.create_personality("metacluster", "nostage", staged=True)

    def test_100_add_utmc1(self):
        command = ["add_metacluster", "--metacluster=utmc1",
                   "--domain=unittest", "--building=ut"]
        self.noouttest(command)

    def test_105_show_utmc1(self):
        command = "show metacluster --metacluster utmc1"
        out = self.commandtest(command.split(" "))
        default_members = self.config.getint("archetype_metacluster",
                                             "max_members_default")
        self.output_equals(out, """
            MetaCluster: utmc1
              Building: ut
                Fullname: Unittest-building
                Address: unittest address
                Location Parents: [Organization ms, Hub ny, Continent na, Country us, Campus ny, City ny]
              Max members: %s
              Build Status: build
              Cluster Personality: metacluster Archetype: metacluster
                Environment: dev
                Owned by GRN: grn:/ms/ei/aquilon/aqd
              Domain: unittest
            """ % default_members, command)

    def test_105_show_utmc1_proto(self):
        command = "show metacluster --metacluster utmc1 --format proto"
        mc = self.protobuftest(command.split(" "), expect=1)[0]
        default_members = self.config.getint("archetype_metacluster",
                                             "max_members_default")
        self.assertEqual(mc.name, "utmc1")
        self.assertEqual(mc.max_members, default_members)
        self.assertEqual(mc.domain.name, "unittest")
        self.assertEqual(mc.domain.type, mc.domain.DOMAIN)
        self.assertEqual(mc.sandbox_author, "")
        self.assertEqual(mc.personality.archetype.name, "metacluster")
        self.assertEqual(mc.personality.name, "metacluster")
        self.assertEqual(mc.status, "build")
        self.assertEqual(mc.virtual_switch.name, "")

    def test_110_add_utmc2(self):
        command = ["add_metacluster", "--prefix=utmc",
                   "--max_members=99", "--building=ut",
                   "--domain=unittest",
                   "--comments", "Some metacluster comments"]
        out = self.commandtest(command)
        self.matchoutput(out, "utmc2", command)

    def test_115_show_utmc2(self):
        command = "show metacluster --metacluster utmc2"
        out = self.commandtest(command.split(" "))
        self.output_equals(out, """
            MetaCluster: utmc2
              Building: ut
                Fullname: Unittest-building
                Address: unittest address
                Location Parents: [Organization ms, Hub ny, Continent na, Country us, Campus ny, City ny]
              Max members: 99
              Build Status: build
              Cluster Personality: metacluster Archetype: metacluster
                Environment: dev
                Owned by GRN: grn:/ms/ei/aquilon/aqd
              Domain: unittest
              Comments: Some metacluster comments
            """, command)

    def test_115_show_utmc2_proto(self):
        command = "show metacluster --metacluster utmc2 --format proto"
        mc = self.protobuftest(command.split(" "), expect=1)[0]
        self.assertEqual(mc.max_members, 99)
        self.assertEqual(mc.location_constraint.name, "ut")
        self.assertEqual(mc.location_constraint.location_type, "building")

    def test_120_add_utmc3(self):
        command = ["add_metacluster", "--metacluster=utmc3",
                   "--max_members=0", "--building=ut", "--domain=unittest",
                   "--comments", "MetaCluster with no members allowed"]
        self.noouttest(command)

    def test_125_show_utmc3(self):
        command = "show metacluster --metacluster utmc3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "MetaCluster: utmc3", command)
        self.matchoutput(out, "Max members: 0", command)
        self.matchoutput(out, "Comments: MetaCluster with no members allowed",
                         command)

    def test_130_add_utmc4(self):
        # Sort of a mini-10 Gig design for port group testing...
        command = ["add_metacluster", "--metacluster=utmc4",
                   "--max_members=6", "--building=ut",
                   "--domain=unittest"]
        self.noouttest(command)

    def test_140_add_utmc7(self):
        # Test moving machines between metaclusters
        command = ["add_metacluster", "--metacluster=utmc7", "--building=ut",
                   "--domain=unittest"]
        self.noouttest(command)

    def test_150_add_sandboxmc(self):
        # Test moving machines between metaclusters
        command = ["add_metacluster", "--metacluster=sandboxmc", "--building=ut",
                   "--sandbox=%s/utsandbox" % self.user]
        self.noouttest(command)

    def test_160_add_metacluster_parameter_defaults(self):
        # Legacy users do not pass --archetype/--domain etc.
        # this should be removed when virtbuild supports new options
        command = ["add_metacluster", "--metacluster=vulcan1"]
        self.noouttest(command)

    def test_170_addutmc8(self):
        self.create_personality("metacluster", "vulcan2")

        command = ["add_metacluster", "--metacluster=utmc8",
                   "--personality=vulcan2", "--archetype=metacluster",
                   "--domain=unittest", "--building=ut",
                   "--comments=autopg_v2_tests"]
        self.noouttest(command)

    def test_171_update_utmc8_vswitch(self):
        self.noouttest(["update_metacluster", "--metacluster", "utmc8",
                        "--virtual_switch", "utvswitch"])

    def test_172_cat_utmc8(self):
        command = ["cat", "--metacluster", "utmc8", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         '"system/metacluster/virtual_switch" = "utvswitch";',
                         command)

    def test_172_show_utmc8_proto(self):
        net = self.net["autopg1"]
        command = ["show_metacluster", "--metacluster", "utmc8",
                   "--format", "proto"]
        mc = self.protobuftest(command, expect=1)[0]
        self.assertEqual(mc.name, "utmc8")
        self.assertEqual(mc.virtual_switch.name, "utvswitch")
        self.assertEqual(len(mc.virtual_switch.portgroups), 1)
        self.assertEqual(mc.virtual_switch.portgroups[0].ip, str(net.ip))
        self.assertEqual(mc.virtual_switch.portgroups[0].cidr, 29)
        self.assertEqual(mc.virtual_switch.portgroups[0].network_tag, 710)
        self.assertEqual(mc.virtual_switch.portgroups[0].usage, "user")

    def test_175_add_utmc9(self):
        # FIXME: Localdisk setups should not have a metacluster, but the
        # templates expect one to exist
        self.create_personality("metacluster", "vulcan-local-disk")

        command = ["add_metacluster", "--metacluster=utmc9",
                   "--personality=vulcan-local-disk", "--archetype=metacluster",
                   "--domain=alt-unittest", "--building=ut",
                   "--comments=vulcan_localdisk_test"]
        self.noouttest(command)

    def test_200_add_utmc1_again(self):
        command = ["add_metacluster", "--metacluster=utmc1",
                   "--building=ut", "--domain=unittest"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Metacluster utmc1 already exists.", command)

    def test_200_nonexistant(self):
        command = "show metacluster --metacluster metacluster-does-not-exist"
        self.notfoundtest(command.split(" "))

    def test_200_global_name(self):
        command = ["add_metacluster", "--metacluster=global", "--building=ut",
                   "--domain=unittest"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "name global is reserved", command)

    def test_200_missing_personality(self):
        command = ["add_metacluster", "--metacluster", "utmc99",
                   "--building", "ut", "--domain", "unittest",
                   "--archetype", "metacluster",
                   "--personality", "no-such-personality"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Personality no-such-personality, archetype "
                         "metacluster not found.", command)

    def test_200_missing_personality_stage(self):
        command = ["add_metacluster", "--metacluster", "utmc99",
                   "--building", "ut", "--domain", "unittest",
                   "--archetype", "metacluster", "--personality", "nostage",
                   "--personality_stage", "previous"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Personality metacluster/nostage does not "
                         "have stage previous.", command)

    def test_200_bad_personality_stage(self):
        command = ["add_metacluster", "--metacluster", "utmc99",
                   "--building", "ut", "--domain", "unittest",
                   "--archetype", "metacluster", "--personality", "nostage",
                   "--personality_stage", "no-such-stage"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "'no-such-stage' is not a valid personality stage.",
                         command)

    def test_300_show_all(self):
        command = "show metacluster --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utmc1", command)
        self.matchoutput(out, "utmc2", command)
        self.matchoutput(out, "utmc3", command)

    def test_300_show_all_proto(self):
        command = "show metacluster --all --format proto"
        mcs = self.protobuftest(command.split(" "))
        names = set(msg.name for msg in mcs)
        for name in ("utmc1", "utmc2", "utmc3"):
            self.assertIn(name, names)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddMetaCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
