#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014,2015  Contributor
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

import unittest
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
        self.noouttest(["add_share", "--cluster=utecl11",
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
        resource = self.protobuftest(command, expect=1)[0]
        self.assertEqual(resource.name, "test_share_1")
        self.assertEqual(resource.type, "share")
        self.assertEqual(resource.share.server, "lnn30f1")
        self.assertEqual(resource.share.mount, "/vol/lnn30f1v1/test_share_1")
        self.assertEqual(resource.share.disk_count, 0)
        self.assertEqual(resource.share.machine_count, 0)

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
        resource = self.protobuftest(command, expect=1)[0]
        self.assertEqual(resource.name, "not_in_nasobjects")
        self.assertEqual(resource.type, "share")
        self.assertFalse(hasattr(resource, 'server'))
        self.assertFalse(hasattr(resource, 'mount'))
        self.assertEqual(resource.share.disk_count, 0)
        self.assertEqual(resource.share.machine_count, 0)

    def test_115_cat_not_in_nasobjects(self):
        command = ["cat", "--cluster=utecl1", "--share=not_in_nasobjects"]
        out = self.commandtest(command)
        self.matchoutput(out, "structure template resource/cluster/utecl1/"
                         "share/not_in_nasobjects/config;",
                         command)
        self.matchoutput(out, '"name" = "not_in_nasobjects";', command)
        self.matchoutput(out, '"server" = null;', command)
        self.matchoutput(out, '"mountpoint" = null;',
                         command)

    def test_130_add_10gig_shares(self):
        for i in range(5, 11):
            self.noouttest(["add_share", "--cluster=utecl%d" % i,
                            "--share=utecl%d_share" % i])

    def test_140_update_no_latency(self):
        command = ["update_share", "--share=test_share_1", "--latency_threshold=0",
                   "--comments=New share comments"]
        out = self.commandtest(command)

    def test_141_verify_no_latency(self):
        command = ["show_share", "--share=test_share_1"]
        out = self.commandtest(command)
        self.matchclean(out, "Latency", command)

    def test_142_verify_no_latency_per_cluster(self):
        for cluster in ("utecl1", "utecl2", "utecl3", "utecl11"):
            command = ["show_share", "--share=test_share_1", "--cluster=%s" % cluster]
            out = self.commandtest(command)
            self.matchclean(out, "Latency", command)

            command = ["cat", "--share=test_share_1", "--cluster=%s" % cluster,
                       "--generate"]
            out = self.commandtest(command)
            self.matchoutput(out, '"name" = "test_share_1";', command)
            self.matchclean(out, 'latency_threshold', command)

    def test_143_set_latency(self):
        command = ["update_share", "--share=test_share_1", "--latency_threshold=20",
                   "--comments=New share comments"]
        out = self.commandtest(command)

    def test_144_verify_test_share_1(self):
        command = ["show_share", "--share=test_share_1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Latency threshold: 20", command)

    def test_145_update_latency(self):
        self.noouttest(["update_share", "--share=test_share_1", "--latency_threshold=30",
                        "--comments=New share comments"])

    def test_146_verify_updated_latency(self):
        for cluster in ("utecl1", "utecl2", "utecl3", "utecl11"):
            command = ["show_share", "--share=test_share_1", "--cluster=%s" % cluster]
            out = self.commandtest(command)
            self.matchoutput(out, "Share: test_share_1", command)
            self.matchoutput(out, "Bound to: ESX Cluster %s" % cluster, command)
            self.matchoutput(out, "Comments: New share comments", command)
            self.matchoutput(out, "Latency threshold: 30", command)

            command = ["cat", "--share=test_share_1", "--cluster=%s" % cluster,
                       "--generate"]
            out = self.commandtest(command)
            self.matchoutput(out, '"name" = "test_share_1";', command)
            self.matchoutput(out, '"latency_threshold" = 30;', command)

    def test_150_add_utmc8_shares(self):
        command = ["add_share", "--resourcegroup=utmc8as1",
                   "--metacluster=utmc8", "--share=test_v2_share"]
        self.noouttest(command)

        command = ["add_share", "--resourcegroup=utmc8as2",
                   "--metacluster=utmc8", "--share=test_v2_share"]
        self.noouttest(command)

    def test_155_show_utmc8as1(self):
        command = ["show_share", "--resourcegroup=utmc8as1",
                   "--metacluster=utmc8", "--share=test_v2_share"]
        out = self.commandtest(command)
        self.matchoutput(out, "Share: test_v2_share", command)
        self.matchoutput(out, "Bound to: Resource Group utmc8as1", command)
        self.matchclean(out, "Latency", command)

        command = ["show_resourcegroup", "--metacluster=utmc8"]
        out = self.commandtest(command)
        self.matchoutput(out, "Resource Group: utmc8as1", command)
        self.matchoutput(out, "Share: test_v2_share", command)

    def test_155_cat_utmc8as1(self):
        command = ["cat", "--resourcegroup=utmc8as1", "--metacluster=utmc8",
                   "--generate"]
        out = self.commandtest(command)
        self.matchoutput(out, "structure template resource/cluster/utmc8/"
                         "resourcegroup/utmc8as1/config;",
                         command)
        self.matchoutput(out, '"name" = "utmc8as1', command)
        self.matchoutput(out,
                         '"resources/share" = '
                         'append(create("resource/cluster/utmc8/resourcegroup/'
                         'utmc8as1/share/test_v2_share/config"));',
                         command)

    def test_155_cat_share(self):
        command = ["cat", "--share=test_v2_share", "--resourcegroup=utmc8as1",
                   "--metacluster=utmc8", "--generate"]
        out = self.commandtest(command)
        self.matchoutput(out, "structure template resource/cluster/utmc8/"
                         "resourcegroup/utmc8as1/share/test_v2_share/config;",
                         command)
        self.matchoutput(out, '"name" = "test_v2_share";', command)
        self.matchoutput(out, '"server" = "lnn30f1";', command)
        self.matchoutput(out, '"mountpoint" = "/vol/lnn30f1v1/test_v2_share";',
                         command)
        self.matchclean(out, 'latency', command)

    def test_155_show_utmc8(self):
        command = "show metacluster --metacluster utmc8"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Share: test_v2_share", command)

    def test_160_add_utmc9(self):
        self.noouttest(["add_share", "--share", "test_v2_share",
                        "--hostname", "evh83.aqd-unittest.ms.com",
                        "--resourcegroup", "utrg2"])

    def test_200_update_nonexistant(self):
        command = ["update_share", "--share=doesnotexist", "--latency_threshold=10",
                   "--comments=New share comments"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Share doesnotexist is not used on any resource"
                         " and cannot be modified", command)

    def test_200_update_bad_latency(self):
        command = ["update_share", "--share=test_share_1", "--latency_threshold=10",
                   "--comments=New share comments"]
        out = self.badrequesttest(command)
        self.matchoutput(out, 'The value of latency_threshold must be either zero, or at least 20.', command)

    def test_200_add_same_share_name(self):
        command = ["add_share", "--resourcegroup=utmc8as2",
                   "--share=test_v2_share"]
        err = self.badrequesttest(command)
        self.matchoutput(err, "Share test_v2_share, "
                         "resource group utmc8as2 already exists.", command)

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

        self.matchoutput(out, "Share: test_v2_share", command)
        self.matchoutput(out, "Bound to: Resource Group utmc8as1", command)
        self.matchoutput(out, "Bound to: Resource Group utmc8as2", command)

    def test_800_cleanup(self):
        # Having a share without a server would blow up compilation, so we need
        # to remove it here
        self.noouttest(["del_share", "--cluster", "utecl1",
                        "--share", "not_in_nasobjects"])

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddShare)
    unittest.TextTestRunner(verbosity=2).run(suite)
