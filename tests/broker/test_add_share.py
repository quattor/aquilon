#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013  Contributor
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

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand

# taken from test_add_service.py
class TestAddShare(TestBrokerCommand):
    def testaddnasshares(self):
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

    # test_share_1 must appear once.
    def testverifyshowutmc1(self):
        command = ["show_metacluster", "--metacluster=utmc1"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r"\s*Share: test_share_1\s*"
                          r"Share: test_share_2\s*"
                          r"Share: test_share_3\s*"
                          r"Share: test_share_4\s*"
                          r"Share: test_share_5\s*"
                          r"Share: test_share_6\s*"
                          r"Share: test_share_7\s*"
                          r"Share: test_share_8", command)

    def testadd10gigshares(self):
        for i in range(5, 11):
            self.noouttest(["add_share", "--cluster=utecl%d" % i,
                            "--share=utecl%d_share" % i])

    def testaddhashares(self):
        for i in range(11, 13):
            self.noouttest(["add_share", "--cluster=utecl%d" % i,
                            "--share=utecl%d_share" % i])
            self.noouttest(["add_share", "--cluster=npecl%d" % i,
                            "--share=npecl%d_share" % i])

    def testverifyshowshare(self):
        command = ["show_share", "--cluster=utecl1", "--share=test_share_1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Share: test_share_1", command)
        self.matchoutput(out, "Bound to: ESX Cluster utecl1", command)

        self.matchoutput(out, "Server: lnn30f1", command)
        self.matchoutput(out, "Mountpoint: /vol/lnn30f1v1/test_share_1",
                         command)
        self.matchoutput(out, "Disk Count: 0", command)
        self.matchoutput(out, "Machine Count: 0", command)
        self.matchclean(out, "Comments", command)
        self.matchclean(out, "Share: test_share_2", command)

    def testverifyshowshareproto(self):
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

    def testverifyshowshareall(self):
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
    def testverifyshowshare(self):
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

    # only backward compatibility - to be removed later.
    def testverifyshowshareall(self):
        command = ["show_nas_disk_share", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "NAS Disk Share: test_share_1", command)
        self.matchoutput(out, "NAS Disk Share: test_share_2", command)
        self.matchoutput(out, "Server: lnn30f1", command)
        self.matchoutput(out, "Mountpoint: /vol/lnn30f1v1/test_share_1",
                         command)
        self.matchoutput(out, "Disk Count: 0", command)
        self.matchoutput(out, "Machine Count: 0", command)

    def testcatshare(self):
        command = ["cat", "--cluster=utecl1", "--share=test_share_1"]
        out = self.commandtest(command)
        self.matchoutput(out, "structure template resource/cluster/utecl1/"
                         "share/test_share_1/config;",
                         command)
        self.matchoutput(out, '"name" = "test_share_1";', command)
        self.matchoutput(out, '"server" = "lnn30f1";', command)
        self.matchoutput(out, '"mountpoint" = "/vol/lnn30f1v1/test_share_1";',
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddShare)
    unittest.TextTestRunner(verbosity=2).run(suite)

