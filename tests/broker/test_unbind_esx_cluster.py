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
"""Module for testing the unbind esx cluster command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUnbindESXCluster(TestBrokerCommand):

    def testfailservicemissingcluster(self):
        command = ["unbind_esx_cluster", "--cluster", "cluster-does-not-exist",
                   "--service=esx_management_server", "--instance=ut.a"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Cluster cluster-does-not-exist not found.",
                         command)

    def testfailservicenotbound(self):
        command = ["unbind_esx_cluster", "--cluster", "utecl1",
                   "--service=utsvc", "--instance=utsi1"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Service Instance utsvc/utsi1 is not bound to "
                         "ESX cluster utecl1.",
                         command)

    def testfailunbindrequiredservice(self):
        command = ["show_esx_cluster", "--cluster=utecl1"]
        out = self.commandtest(command)
        m = self.searchoutput(out,
                              r'Member Alignment: Service '
                              r'esx_management_server Instance (\S+)',
                              command)
        instance = m.group(1)

        command = ["unbind_esx_cluster", "--cluster=utecl1",
                   "--service=esx_management_server",
                   "--instance=%s" % instance]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Cannot remove cluster service instance binding for "
                         "esx cluster aligned service esx_management_server.",
                         command)

    def testunbindservice(self):
        # This also tests binding a non-aligned service...
        # not sure if there should be a test of running make against a
        # cluster (or a cluster with hosts) while bound to such a service...
        command = ["bind_esx_cluster", "--cluster=utecl4",
                   "--service=utsvc", "--instance=utsi1"]
        (out, err) = self.successtest(command)

        command = ["unbind_esx_cluster", "--cluster=utecl4",
                   "--service=utsvc", "--instance=utsi1"]
        out = self.commandtest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUnbindESXCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
