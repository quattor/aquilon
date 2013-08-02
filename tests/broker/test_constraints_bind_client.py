#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2012,2013  Contributor
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
"""Module for testing constraints involving the bind client command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestBindClientConstraints(TestBrokerCommand):

    def testrebindfails(self):
        command = ["bind", "client",
                   "--hostname", "unittest02.one-nyp.ms.com",
                   "--service", "utsvc", "--instance", "utsi1"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "is already bound", command)

    def testfailbindclusteralignedservice(self):
        # Figure out which service the cluster is bound to and attempt change.
        command = ["show_esx_cluster", "--cluster=utecl1"]
        out = self.commandtest(command)
        m = self.searchoutput(out,
                              r'Member Alignment: Service '
                              r'esx_management_server Instance (\S+)',
                              command)
        instance = m.group(1)
        # Grab a host from the cluster
        command = ["search_host", "--cluster=utecl1"]
        out = self.commandtest(command)
        m = self.searchoutput(out, r'(\S+)', command)
        host = m.group(1)
        # Sanity check that the host is currently aligned.
        command = ["search_host", "--host=%s" % host,
                   "--service=esx_management_server",
                   "--instance=%s" % instance]
        out = self.commandtest(command)
        self.matchoutput(out, host, command)
        # Now try to swap.
        next = instance == 'ut.a' and 'ut.b' or 'ut.a'
        command = ["bind_client", "--hostname=%s" % host,
                   "--service=esx_management_server", "--instance=%s" % next]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "ESX Cluster utecl1 is set to use service "
                         "instance esx_management_server/%s" % instance,
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(
        TestBindClientConstraints)
    unittest.TextTestRunner(verbosity=2).run(suite)
