#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014  Contributor
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
"""Module for testing the bind esx cluster command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestBindESXCluster(TestBrokerCommand):

    def testfailbindservicemissingcluster(self):
        command = ["bind_esx_cluster", "--cluster=cluster-does-not-exist",
                   "--service=esx_management_server", "--instance=ut.a"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Cluster cluster-does-not-exist not found.",
                         command)

    def testfailbindservicenotrebind(self):
        # Figure out which service the cluster is bound to and attempt change.
        command = ["show_esx_cluster", "--cluster=utecl1"]
        out = self.commandtest(command)
        m = self.searchoutput(out,
                              r'Member Alignment: Service '
                              r'esx_management_server Instance (\S+)',
                              command)
        next = m.group(1) == 'ut.a' and 'ut.b' or 'ut.a'
        command = ["bind_esx_cluster", "--cluster=utecl1",
                   "--service=esx_management_server", "--instance=%s" % next]
        out = self.badrequesttest(command)
        self.matchoutput(out, "use unbind to clear first or rebind to force",
                         command)

    def testrebindservice(self):
        # Figure out which service the cluster is bound to and attempt change.
        command = ["show_esx_cluster", "--cluster=utecl1"]
        out = self.commandtest(command)
        m = self.searchoutput(out,
                              r'Member Alignment: Service '
                              r'esx_management_server Instance (\S+)',
                              command)
        next = m.group(1) == 'ut.a' and 'ut.b' or 'ut.a'

        command = ["rebind_esx_cluster", "--cluster=utecl1",
                   "--service=esx_management_server", "--instance=%s" % next]
        # Do we need any checks on this output?
        (out, err) = self.successtest(command)

        command = ["show_esx_cluster", "--cluster=utecl1"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Member Alignment: Service esx_management_server "
                         "Instance %s" % next,
                         command)

        command = ["search_host", "--cluster=utecl1"]
        out = self.commandtest(command)
        members = sorted(out.splitlines())
        self.failUnless(members, "No hosts in output of %s." % command)

        command = ["search_host", "--cluster=utecl1",
                   "--service=esx_management_server", "--instance=%s" % next]
        out = self.commandtest(command)
        aligned = sorted(out.splitlines())
        self.failUnlessEqual(members, aligned,
                             "Not all cluster members (%s) are aligned (%s)." %
                             (members, aligned))

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBindESXCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
