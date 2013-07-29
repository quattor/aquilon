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
"""Module for testing the uncluster command."""

import unittest

if __name__ == "__main__":
    from broker import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUncluster(TestBrokerCommand):

    def testfailunbindevh1(self):
        command = ["uncluster",
                   "--hostname", "evh1.aqd-unittest.ms.com",
                   "--cluster", "utecl1"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Host evh1.aqd-unittest.ms.com is bound to "
                         "ESX cluster utecl2, not ESX cluster utecl1.",
                         command)

    def testunclusterpersonality(self):
        command = ["uncluster",
                   "--hostname", "evh1.aqd-unittest.ms.com",
                   "--cluster", "utecl2",
                   "--personality", "esx_server"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Cannot switch host to personality "
                         "esx_server because that personality "
                         "requires a cluster",
                         command)

        command = ["uncluster",
                   "--hostname", "evh1.aqd-unittest.ms.com",
                   "--cluster", "utecl2",
                   "--personality", "esx_standalone"]
        self.successtest(command)

    def testunbindutecl1(self):
        for i in range(2, 5):
            hostname = 'evh%s.aqd-unittest.ms.com' % i
            self.verify_buildfiles('utsandbox', hostname, want_exist=True,
                                   command='uncluster')
            self.noouttest(['uncluster', '--personality', 'generic',
                            '--hostname', hostname, '--cluster', 'utecl1'])
            # We declare that personality generic is OK without a cluster,
            # so the build files should still be there.
            self.verify_buildfiles('utsandbox', hostname, want_exist=True,
                                   command='uncluster')

    def testverifycat(self):
        command = "cat --cluster utecl1 --data"
        out = self.commandtest(command.split())
        self.searchoutput(out, r'"system/cluster/members" = list\(\s*\);', command)

    def testunbindutecl2(self):
        self.noouttest(["uncluster", "--hostname", "evh5.aqd-unittest.ms.com",
                        "--cluster", "utecl2", "--personality", "generic"])

    def testverifyunbindhosts(self):
        for i in range(1, 6):
            command = "show host --hostname evh%s.aqd-unittest.ms.com" % i
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, "Primary Name: evh%s.aqd-unittest.ms.com" % i,
                             command)
            self.matchclean(out, "Member of ESX Cluster", command)

    def testfailmissingcluster(self):
        command = ["uncluster", "--hostname=evh9.aqd-unittest.ms.com",
                   "--cluster", "cluster-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Cluster cluster-does-not-exist not found.",
                         command)

    def testfailunboundcluster(self):
        command = ["uncluster",
                   "--hostname=evh9.aqd-unittest.ms.com",
                   "--cluster", "utecl1"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "not bound to a cluster", command)

    def testunbindutmc4(self):
        for i in range(1, 25):
            host = "evh%s.aqd-unittest.ms.com" % (i + 50)
            cluster = "utecl%d" % (5 + ((i - 1) / 4))
            self.noouttest(["uncluster", "--personality", "generic",
                            "--hostname", host, "--cluster", cluster])

    def testunbindutstorage1(self):
        command = ["uncluster",
                   "--hostname=filer1.ms.com",
                   "--cluster=utstorage1"]
        self.successtest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUncluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
