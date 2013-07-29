#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
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
"""Module for testing GRN mapping."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from broker.brokertest import TestBrokerCommand
from broker.grntest import VerifyGrnsMixin

GRN = "grn:/ms/ei/aquilon/unittest"


class TestMapGrn(VerifyGrnsMixin, TestBrokerCommand):

    grn_list = ["grn:/ms/ei/aquilon/aqd", "grn:/ms/ei/aquilon/unittest"]
    grn_maps = {"esp": grn_list, "atarget": ["grn:/example/cards"]}

    def test_100_add_personality(self):
        command = ["add_personality", "--personality=utesppers/dev",
                   "--archetype=aquilon", "--grn=%s" % GRN,
                   "--host_environment=dev",
                   "--comments", "Personality target test"]
        self.noouttest(command)

        command = ["show_personality", "--personality=utesppers/dev",
                   "--archetype=aquilon"]
        out = self.commandtest(command)
        self.matchoutput(out, "Used by GRN: grn:/ms/ei/aquilon/unittest [esp]",
                         command)

        command = ["del_personality", "--personality=utesppers/dev",
                   "--archetype=aquilon"]
        self.noouttest(command)

    def test_100_map_bad_personality(self):
        command = ["map", "grn", "--grn", "grn:/ms/ei/aquilon/aqd",
                   "--personality", "compileserver", "--target", "badtarget"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Invalid personality target badtarget for "
                              "archetype aquilon, please choose from "
                              "esp,hlmplus", command)

    def test_105_map_personality(self):
        command = ["map", "grn", "--grn", "grn:/ms/ei/aquilon/aqd",
                   "--personality", "compileserver", "--target", "esp"]
        self.successtest(command)

        command = ["map", "grn", "--grn", "grn:/example/cards",
                   "--personality", "compileserver", "--target", "atarget"]
        self.successtest(command)

    def test_110_verify_personality(self):
        command = ["show", "personality", "--personality", "compileserver"]
        out = self.commandtest(command)
        self.matchoutput(out, "GRN: grn:/ms/ei/aquilon/aqd [esp]", command)

        command = ["cat", "--archetype=aquilon", "--personality=compileserver"]
        out = self.commandtest(command)
        self.check_personality_grns(out, self.grn_maps["esp"], self.grn_maps,
                                    command)

    def test_120_verify_host(self):
        command = ["show_host", "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "GRN: grn:/ms/ei/aquilon/aqd [esp]", command)

    def test_130_map_host(self):
        command = ["map", "grn", "--grn", "grn:/ms/ei/aquilon/aqd",
                   "--hostname", "unittest12.aqd-unittest.ms.com",
                   "--target", "esp"]
        self.noouttest(command)

    def test_131_map_host_again(self):
        scratchfile = self.writescratch("hostlist",
                                        "unittest12.aqd-unittest.ms.com")
        command = ["map", "grn", "--grn", "grn:/ms/ei/aquilon/aqd",
                   "--list", scratchfile, "--target", "esp"]
        # TODO: should this throw an error?
        self.noouttest(command)

    def test_132_map_host_plus_pers(self):
        # The personality already includes the GRN
        command = ["map", "grn", "--grn", "grn:/ms/ei/aquilon/aqd",
                   "--hostname", "unittest00.one-nyp.ms.com", "--target", "esp"]
        self.noouttest(command)

        command = ["map", "grn", "--grn", "grn:/example/cards",
                   "--hostname", "unittest00.one-nyp.ms.com", "--target", "atarget"]
        self.noouttest(command)

    def test_140_search(self):
        command = ["search", "host", "--grn", "grn:/ms/ei/aquilon/aqd"]
        out = self.commandtest(command)
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest20.aqd-unittest.ms.com", command)
        self.matchoutput(out, "unittest12.aqd-unittest.ms.com", command)

    def test_150_map_disabled(self):
        command = ["map", "grn", "--grn", "grn:/ms/ei/aquilon",
                   "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--target", "esp"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "GRN grn:/ms/ei/aquilon is not usable for new "
                         "systems.", command)

    def test_160_map_missing_eonid(self):
        command = ["map", "grn", "--eon_id", "987654321", "--target", "esp",
                   "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "EON ID 987654321 not found.", command)
        # The EON ID is not in the CDB file, so the CSV file should not be
        # parsed
        self.matchclean(out, "acquiring", command)

    def test_160_map_missing_grn(self):
        command = ["map", "grn", "--grn", "grn:/ms/no-such-grn",
                   "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--target", "esp"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "GRN grn:/ms/no-such-grn not found.", command)
        # The GRN is not in the CDB file, so the CSV file should not be
        # parsed
        self.matchclean(out, "acquiring", command)

    def test_200_verify_unittest00(self):
        command = ["cat", "--hostname", "unittest00.one-nyp.ms.com", "--data",
                   "--generate"]
        out = self.commandtest(command)
        # The GRN is mapped to both the host and the personality; verify it is
        # not duplicated. Should print out both the host mapped
        # personality mapped grns
        self.check_grns(out, self.grn_maps["esp"], self.grn_maps, command)

    def test_210_verify_unittest20(self):
        command = ["cat", "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--data", "--generate"]
        out = self.commandtest(command)
        # The GRN is mapped to the personality only
        self.check_grns(out, self.grn_list, {"esp": self.grn_list}, command)

    def test_220_verify_unittest12(self):
        command = ["cat", "--hostname", "unittest12.aqd-unittest.ms.com",
                   "--data", "--generate"]
        out = self.commandtest(command)
        # The GRN is mapped to the host only
        self.check_grns(out, self.grn_list, {"esp": self.grn_list}, command)

    def test_300_delete_used_byhost(self):
        command = ["del", "grn", "--grn", "grn:/ms/ei/aquilon/aqd"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "GRN grn:/ms/ei/aquilon/aqd is still used by "
                         "hosts, and cannot be deleted.", command)

    def test_310_delete_missing(self):
        command = ["del", "grn", "--eon_id", "987654321"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "EON ID 987654321 not found.", command)

    def test_320_unmap_unittest12(self):
        command = ["unmap", "grn", "--grn", "grn:/ms/ei/aquilon/aqd",
                   "--hostname", "unittest12.aqd-unittest.ms.com",
                   "--target", "esp"]
        self.noouttest(command)

    def test_320_unmap_unittest00(self):
        command = ["unmap", "grn", "--grn", "grn:/ms/ei/aquilon/aqd",
                   "--hostname", "unittest00.one-nyp.ms.com", "--target", "esp"]
        self.noouttest(command)

    def test_321_verify_unittest12(self):
        command = ["show_host", "--hostname", "unittest12.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        # Make sure not to match the personality GRN
        self.searchclean(out, r"^  GRN", command)

    def test_322_verify_search(self):
        command = ["search", "host", "--grn", "grn:/ms/ei/aquilon/aqd"]
        out = self.commandtest(command)
        # unittest00 is still included due to its personality
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest20.aqd-unittest.ms.com", command)
        self.matchclean(out, "unittest12.aqd-unittest.ms.com", command)

    def test_325_unmap_host_again(self):
        scratchfile = self.writescratch("hostlist",
                                        "unittest12.aqd-unittest.ms.com")
        command = ["unmap", "grn", "--grn", "grn:/ms/ei/aquilon/aqd",
                   "--list", scratchfile, "--target", "esp"]
        # TODO: should this throw an error?
        self.noouttest(command)

    def test_330_delete_used_bypers(self):
        command = ["del", "grn", "--grn", "grn:/ms/windows/desktop"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "GRN grn:/ms/windows/desktop is still used "
                         "by personalities, and cannot be deleted.", command)

    def test_340_unmap_personality(self):
        command = ["unmap", "grn", "--grn", "grn:/example/cards",
                   "--personality", "compileserver", "--target", "atarget"]
        self.noouttest(command)

        command = ["cat", "--archetype", "aquilon",
                   "--personality", "compileserver"]
        out = self.commandtest(command)

        grn_list = ["grn:/ms/ei/aquilon/aqd", "grn:/ms/ei/aquilon/unittest"]
        self.check_personality_grns(out, grn_list, {"esp": grn_list}, command)

        command = ["unmap", "grn", "--grn", "grn:/ms/ei/aquilon/aqd",
                   "--personality", "compileserver", "--target", "esp"]
        self.noouttest(command)

    def test_400_verify_unittest00(self):
        command = ["cat", "--hostname", "unittest00.one-nyp.ms.com", "--data",
                   "--generate"]
        out = self.commandtest(command)
        # The GRN was mapped to both the host and the personality;
        self.check_grns(out, ["grn:/ms/ei/aquilon/unittest"],
                        {"esp": ["grn:/ms/ei/aquilon/unittest"]},
                        command)

    def test_410_verify_unittest20(self):
        command = ["cat", "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--data", "--generate"]
        out = self.commandtest(command)
        # The GRN was mapped to the personality only
        self.check_grns(out, ["grn:/ms/ei/aquilon/unittest"],
                        {"esp": ["grn:/ms/ei/aquilon/unittest"]},
                        command)

    def test_420_verify_unittest12(self):
        command = ["cat", "--hostname", "unittest12.aqd-unittest.ms.com",
                   "--data", "--generate"]
        out = self.commandtest(command)
        # The GRN was mapped to the host only
        self.check_grns(out, ["grn:/ms/ei/aquilon/unittest"],
                        {"esp": ["grn:/ms/ei/aquilon/unittest"]},
                        command)

    def test_500_fail_map_overlimitlist(self):
        user = self.config.get("unittest", "user")
        hostlimit = self.config.getint("broker", "map_grn_max_list_size")
        hosts = []
        for i in range(1, 20):
            hosts.append("thishostdoesnotexist%d.aqd-unittest.ms.com\n" % i)
        scratchfile = self.writescratch("mapgrnlistlimit", "".join(hosts))
        command = ["map", "grn", "--grn", "grn:/ms/ei/aquilon/aqd",
                   "--list", scratchfile, "--target", "esp"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The number of hosts in list {0:d} can not be more "
                         "than {1:d}".format(len(hosts), hostlimit),
                         command)

    def test_500_fail_unmap_overlimitlist(self):
        user = self.config.get("unittest", "user")
        hostlimit = self.config.getint("broker", "unmap_grn_max_list_size")
        hosts = []
        for i in range(1, 20):
            hosts.append("thishostdoesnotexist%d.aqd-unittest.ms.com\n" % i)
        scratchfile = self.writescratch("mapgrnlistlimit", "".join(hosts))
        command = ["unmap", "grn", "--grn", "grn:/ms/ei/aquilon/aqd",
                   "--list", scratchfile, "--target", "esp"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The number of hosts in list {0:d} can not be more "
                         "than {1:d}".format(len(hosts), hostlimit),
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMapGrn)
    unittest.TextTestRunner(verbosity=2).run(suite)
