#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010,2011  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Module for testing the bind esx cluster command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestBindESXCluster(TestBrokerCommand):

    def testdeprecation(self):
        # This same test exists in the test_cluster module, and can be
        # removed here if/when the bind_esx_cluster --hostname option is
        # removed.
        command = ["bind_esx_cluster", "--hostname=evh9.aqd-unittest.ms.com",
                   "--cluster", "cluster-does-not-exist"]
        (p, out, err) = self.runcommand(command)
        self.matchoutput(err,
                         "The --hostname option is deprecated.  "
                         "Please use the 'cluster' command instead.",
                         command)

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
        members = out.splitlines()
        members.sort()
        self.failUnless(members, "No hosts in output of %s." % command)

        command = ["search_host", "--cluster=utecl1",
                   "--service=esx_management_server", "--instance=%s" % next]
        out = self.commandtest(command)
        aligned = out.splitlines()
        aligned.sort()
        self.failUnlessEqual(members, aligned,
                             "Not all cluster members (%s) are aligned (%s)." %
                             (members, aligned))

if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBindESXCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
