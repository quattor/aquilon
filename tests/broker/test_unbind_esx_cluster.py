#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010  Contributor
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
"""Module for testing the unbind esx cluster command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUnbindESXCluster(TestBrokerCommand):

    def testfailunbindevh1(self):
        # This test is duplicated in uncluster, but here it is testing the
        # deprecation warning.  This test can be removed if/when the
        # --hostname option is removed from unbind_esx_cluster.
        command = ["unbind_esx_cluster",
                   "--hostname", "evh1.aqd-unittest.ms.com",
                   "--cluster", "utecl1"]
        (p, out, err) = self.runcommand(command)
        self.matchoutput(err,
                         "WARNING: unbind_esx_cluster --hostname is "
                         "deprecated, use the uncluster command instead.",
                         command)

    def testfailservicemissingcluster(self):
        command = ["unbind_esx_cluster", "--cluster", "cluster-does-not-exist",
                   "--service=esx_management_server", "--instance=ut.a"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "ESX Cluster cluster-does-not-exist not found.",
                         command)

    def testfailservicenotbound(self):
        command = ["unbind_esx_cluster", "--cluster", "utecl1",
                   "--service=utsvc", "--instance=utsi1"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Cluster Service Binding ESX cluster utecl1, "
                         "service instance utsvc/utsi1 not found.",
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


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUnbindESXCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
