#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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
"""Module for testing the rebind metacluster command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestRebindMetaCluster(TestBrokerCommand):

    def testfailinvalidcluster(self):
        command = ["rebind_metacluster", "--cluster=cluster-does-not-exist",
                   "--metacluster=utmc1"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Cluster cluster-does-not-exist not found.",
                         command)

    def testfailinvalidmetacluster(self):
        command = ["rebind_metacluster", "--cluster=utecl1",
                   "--metacluster=metacluster-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Metacluster metacluster-does-not-exist not found.",
                         command)

    def testfailfullmetacluster(self):
        command = ["rebind_metacluster", "--cluster=utecl4",
                   "--metacluster=utmc3"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Metacluster utmc3 already has the maximum "
                         "number of clusters (0).", command)

    def testrebindutecl3(self):
        command = ["rebind_metacluster", "--cluster=utecl3",
                   "--metacluster=utmc1"]
        self.noouttest(command)

    def testverifyrebindutecl3(self):
        command = ["cat", "--cluster=utecl3"]
        out = self.commandtest(command)
        self.matchoutput(out, "object template clusters/utecl3;", command)
        self.matchoutput(out, "'/system/cluster/name' = 'utecl3';", command)
        self.matchoutput(out, "'/system/metacluster/name' = 'utmc1';", command)
        self.searchoutput(out, r"'/system/cluster/machines' = nlist\(\s*\);",
                          command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRebindMetaCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)

