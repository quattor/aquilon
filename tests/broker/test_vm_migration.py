#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015  Contributor
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
'Module for testing moving VMs around.'

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestVMMigration(TestBrokerCommand):

    def test_100_metacluster_change_pre(self):
        command = ["show_share", "--all"]
        out = self.commandtest(command)
        # Initially the VM is on utecl1, test_share_1 is not used on utecl11
        self.searchoutput(out,
                          r'Share: test_share_1\s*'
                          r'Comments: New share comments\s*'
                          r'Bound to: ESX Cluster utecl1\s*'
                          r'Latency threshold: 30\s*'
                          r'Server: lnn30f1\s*'
                          r'Mountpoint: /vol/lnn30f1v1/test_share_1\s*'
                          r'Disk Count: 1\s*'
                          r'Machine Count: 1\s*',
                          command)
        self.searchoutput(out,
                          r'Share: test_share_1\s*'
                          r'Comments: New share comments\s*'
                          r'Bound to: ESX Cluster utecl11\s*'
                          r'Latency threshold: 30\s*'
                          r'Server: lnn30f1\s*'
                          r'Mountpoint: /vol/lnn30f1v1/test_share_1\s*'
                          r'Disk Count: 0\s*'
                          r'Machine Count: 0\s*',
                          command)

    def test_101_metacluster_change(self):
        old_path = ["machine", "americas", "ut", "ut10", "evm1"]
        new_path = ["machine", "americas", "ut", "None", "evm1"]
        command = ["update_machine", "--machine=evm1", "--cluster=utecl11",
                   "--allow_metacluster_change"]
        self.noouttest(command)
        self.check_plenary_gone(*old_path)
        self.check_plenary_exists(*new_path)

    def test_105_verify_shares(self):
        command = ["show_share", "--all"]
        out = self.commandtest(command)

        # The disk should have moved to utecl11, test_share_1 should be unused on
        # utecl1
        self.searchoutput(out,
                          r'Share: test_share_1\s*'
                          r'Comments: New share comments\s*'
                          r'Bound to: ESX Cluster utecl1\s*'
                          r'Latency threshold: 30\s*'
                          r'Server: lnn30f1\s*'
                          r'Mountpoint: /vol/lnn30f1v1/test_share_1\s*'
                          r'Disk Count: 0\s*'
                          r'Machine Count: 0\s*',
                          command)
        self.searchoutput(out,
                          r'Share: test_share_1\s*'
                          r'Comments: New share comments\s*'
                          r'Bound to: ESX Cluster utecl11\s*'
                          r'Latency threshold: 30\s*'
                          r'Server: lnn30f1\s*'
                          r'Mountpoint: /vol/lnn30f1v1/test_share_1\s*'
                          r'Disk Count: 1\s*'
                          r'Machine Count: 1\s*',
                          command)

    def test_105_verify_search_machine(self):
        command = ["search_machine", "--machine=evm1", "--cluster=utecl11"]
        out = self.commandtest(command)
        self.matchoutput(out, "evm1", command)

    def test_109_revert_metacluster_change(self):
        command = ["update_machine", "--machine=evm1", "--cluster=utecl1",
                   "--allow_metacluster_change"]
        # restore
        self.noouttest(command)

    def test_200_missing_cluster(self):
        command = ["update_machine", "--machine=evm1",
                   "--cluster=cluster-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Cluster cluster-does-not-exist not found.",
                         command)

    def test_200_change_metacluster(self):
        command = ["update_machine", "--machine=evm1", "--cluster=utecl11"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Moving VMs between metaclusters is disabled by "
                         "default.",
                         command)

    def test_200_cluster_full(self):
        command = ["update_machine", "--machine=evm1", "--cluster=utecl3"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "ESX Cluster utecl3 cannot support VMs with "
                         "0 vmhosts and a down_hosts_threshold of 2",
                         command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestVMMigration)
    unittest.TextTestRunner(verbosity=2).run(suite)
