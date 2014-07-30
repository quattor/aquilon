#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014  Contributor
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
"""Module for testing the add service command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestAddShare(TestBrokerCommand):
    def test_100_add_shares(self):
        # Creates shares test_share_1 through test_share_9
        for i in range(1, 9):
            self.noouttest(["add_share", "--cluster=utecl1",
                            "--share=test_share_%s" % i])

        self.noouttest(["add_share", "--cluster=utecl2",
                        "--share=test_share_1"])
        self.noouttest(["add_share", "--cluster=utecl3",
                        "--share=test_share_1"])
        self.noouttest(["add_share", "--cluster=utecl13",
                        "--share=test_share_1"])

    def test_105_show_test_share_1(self):
        command = ["show_share", "--cluster=utecl1", "--share=test_share_1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Share: test_share_1", command)
        self.matchoutput(out, "Bound to: ESX Cluster utecl1", command)

        self.matchoutput(out, "Server: lnn30f1", command)
        self.matchoutput(out, "Mountpoint: /vol/lnn30f1v1/test_share_1",
                         command)
        self.matchoutput(out, "Disk Count: 0", command)
        self.matchoutput(out, "Machine Count: 0", command)
        self.matchclean(out, "Latency", command)
        self.matchclean(out, "Comments", command)
        self.matchclean(out, "Share: test_share_2", command)

    def test_105_show_test_share_1_proto(self):
        command = ["show_share", "--cluster=utecl1", "--share=test_share_1",
                   "--format", "proto"]
        out = self.commandtest(command)
        reslist = self.parse_resourcelist_msg(out, expect=1)
        resource = reslist.resources[0]
        self.failUnlessEqual(resource.name, "test_share_1")
        self.failUnlessEqual(resource.type, "share")
        self.failUnlessEqual(resource.share.server, "lnn30f1")
        self.failUnlessEqual(resource.share.mount,
                             "/vol/lnn30f1v1/test_share_1")
        self.failUnlessEqual(resource.share.disk_count, 0)
        self.failUnlessEqual(resource.share.machine_count, 0)

    def test_105_cat_test_share_1(self):
        command = ["cat", "--cluster=utecl1", "--share=test_share_1"]
        out = self.commandtest(command)
        self.matchoutput(out, "structure template resource/cluster/utecl1/"
                         "share/test_share_1/config;",
                         command)
        self.matchoutput(out, '"name" = "test_share_1";', command)
        self.matchoutput(out, '"server" = "lnn30f1";', command)
        self.matchoutput(out, '"mountpoint" = "/vol/lnn30f1v1/test_share_1";',
                         command)

    # only backward compatibility - to be removed later.
    def test_105_show_nas_disk_share(self):
        command = ["show_nas_disk_share", "--share=test_share_1"]
        out = self.commandtest(command)
        self.matchoutput(out, "NAS Disk Share: test_share_1", command)
        self.matchoutput(out, "Server: lnn30f1", command)
        self.matchoutput(out, "Mountpoint: /vol/lnn30f1v1/test_share_1",
                         command)
        self.matchoutput(out, "Disk Count: 0", command)
        self.matchoutput(out, "Machine Count: 0", command)
        self.matchclean(out, "Comments", command)
        self.matchclean(out, "NAS Disk Share: test_share_2", command)

    def test_110_add_not_in_nasobjects(self):
        self.noouttest(["add_share", "--cluster", "utecl1",
                        "--share", "not_in_nasobjects"])

    def test_115_verify_not_in_nasobjects(self):
        command = ["show_share", "--cluster", "utecl1",
                   "--share", "not_in_nasobjects"]
        out = self.commandtest(command)
        self.matchoutput(out, "Share: not_in_nasobjects", command)
        self.matchoutput(out, "Server: None", command)
        self.matchoutput(out, "Mountpoint: None", command)

    def test_115_verify_not_in_nasobjects_proto(self):
        command = ["show_share", "--cluster", "utecl1",
                   "--share", "not_in_nasobjects", "--format", "proto"]
        out = self.commandtest(command)
        reslist = self.parse_resourcelist_msg(out, expect=1)
        resource = reslist.resources[0]
        self.failUnlessEqual(resource.name, "not_in_nasobjects")
        self.failUnlessEqual(resource.type, "share")
        self.failIf(hasattr(resource, 'server'))
        self.failIf(hasattr(resource, 'mount'))
        self.failUnlessEqual(resource.share.disk_count, 0)
        self.failUnlessEqual(resource.share.machine_count, 0)

    def test_130_add_10gig_shares(self):
        for i in range(5, 11):
            self.noouttest(["add_share", "--cluster=utecl%d" % i,
                            "--share=utecl%d_share" % i])

    def test_140_add_ha_shares(self):
        for i in range(11, 13):
            self.noouttest(["add_share", "--cluster=utecl%d" % i,
                            "--share=utecl%d_share" % i])
            self.noouttest(["add_share", "--cluster=npecl%d" % i,
                            "--share=npecl%d_share" % i])

    def test_150_update_no_latency(self):
        command = ["update_share", "--share=test_share_1", "--latency_threshold=0",
                   "--comments=updated comment"]
        out = self.commandtest(command)

    def test_151_verify_no_latency(self):
        command = ["show_share", "--share=test_share_1"]
        out = self.commandtest(command)
        self.matchclean(out, "Latency", command)

    def test_152_verify_no_latency_per_cluster(self):
        for cluster in ("utecl1", "utecl2", "utecl3", "utecl13"):
            command = ["show_share", "--share=test_share_1", "--cluster=%s" % cluster]
            out = self.commandtest(command)
            self.matchclean(out, "Latency", command)

            command = ["cat", "--share=test_share_1", "--cluster=%s" % cluster,
                       "--generate"]
            out = self.commandtest(command)
            self.matchoutput(out, '"name" = "test_share_1";', command)
            self.matchclean(out, 'latency_threshold', command)

    def test_153_set_latency(self):
        command = ["update_share", "--share=test_share_1", "--latency_threshold=20",
                   "--comments=updated comment"]
        out = self.commandtest(command)

    def test_154_verify_test_share_1(self):
        command = ["show_share", "--share=test_share_1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Latency threshold: 20", command)

    def test_155_update_latency(self):
        self.noouttest(["update_share", "--share=test_share_1", "--latency_threshold=30",
                        "--comments=updated comment"])

    def test_156_verify_updated_latency(self):
        for cluster in ("utecl1", "utecl2", "utecl3", "utecl13"):
            command = ["show_share", "--share=test_share_1", "--cluster=%s" % cluster]
            out = self.commandtest(command)
            self.matchoutput(out, "Share: test_share_1", command)
            self.matchoutput(out, "Bound to: ESX Cluster %s" % cluster, command)
            self.matchoutput(out, "Comments: updated comment", command)
            self.matchoutput(out, "Latency threshold: 30", command)

            command = ["cat", "--share=test_share_1", "--cluster=%s" % cluster,
                       "--generate"]
            out = self.commandtest(command)
            self.matchoutput(out, '"name" = "test_share_1";', command)
            self.matchoutput(out, '"latency_threshold" = 30;', command)

    def test_200_update_nonexistant(self):
        command = ["update_share", "--share=doesnotexist", "--latency_threshold=10",
                   "--comments=updated comment"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Share doesnotexist is not used on any resource"
                         " and cannot be modified", command)

    def test_200_update_bad_latency(self):
        command = ["update_share", "--share=test_share_1", "--latency_threshold=10",
                   "--comments=updated comment"]
        out = self.badrequesttest(command)
        self.matchoutput(out, 'The value of latency_threshold must be either zero, or at least 20.', command)

    # test_share_1 must appear once.
    def test_300_verify_utmc1(self):
        command = ["show_metacluster", "--metacluster=utmc1"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r"Share: not_in_nasobjects\s*"
                          r"Share: test_share_1\s*"
                          r"Share: test_share_2\s*"
                          r"Share: test_share_3\s*"
                          r"Share: test_share_4\s*"
                          r"Share: test_share_5\s*"
                          r"Share: test_share_6\s*"
                          r"Share: test_share_7\s*"
                          r"Share: test_share_8", command)

    def test_310_show_share_all(self):
        command = ["show_share", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Share: test_share_1", command)
        self.matchoutput(out, "Share: test_share_2", command)
        self.matchoutput(out, "Server: lnn30f1", command)
        self.matchoutput(out, "Mountpoint: /vol/lnn30f1v1/test_share_1",
                         command)
        self.matchoutput(out, "Disk Count: 0", command)
        self.matchoutput(out, "Machine Count: 0", command)

    # only backward compatibility - to be removed later.
    def test_320_show_nas_disk_share_all(self):
        command = ["show_nas_disk_share", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "NAS Disk Share: test_share_1", command)
        self.matchoutput(out, "NAS Disk Share: test_share_2", command)
        self.matchoutput(out, "Server: lnn30f1", command)
        self.matchoutput(out, "Mountpoint: /vol/lnn30f1v1/test_share_1",
                         command)
        self.matchoutput(out, "Disk Count: 0", command)
        self.matchoutput(out, "Machine Count: 0", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddShare)
    unittest.TextTestRunner(verbosity=2).run(suite)
