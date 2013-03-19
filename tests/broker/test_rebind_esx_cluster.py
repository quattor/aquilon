#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Module for testing using the cluster command to move between clusters."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


# Note, this used to test the rebind_esx_cluster, however I've
# deco'ed that command. I've kept this test here in order to preserve
# the state of all the previous and subsequent tests that assume the
# state of evh1 (it's a tangled web of statefulness going on here!)

class TestRebindESXCluster(TestBrokerCommand):

    # Failure test is in add_virtual_hardware.
    def test_100_rebind_evh1(self):
        self.successtest(["cluster",
                          "--hostname", "evh1.aqd-unittest.ms.com",
                          "--cluster", "utecl2"])

    def test_110_unbind_evh2(self):
        # Let's see if we can put a node back after the cluster size has shrunk
        command = ["uncluster", "--hostname", "evh2.aqd-unittest.ms.com",
                   "--personality", "generic", "--cluster", "utecl1"]
        self.successtest(command)

    def test_111_rebind_evh2(self):
        command = ["cluster", "--hostname", "evh2.aqd-unittest.ms.com",
                   "--personality", "vulcan-1g-desktop-prod",
                   "--cluster", "utecl1"]
        self.successtest(command)

    def test_200_verifyrebindevh1(self):
        command = "show host --hostname evh1.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Primary Name: evh1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Member of ESX Cluster: utecl2", command)

        # FIXME: Also test plenary files.

    def test_200_verify_evh2(self):
        command = ["show", "cluster", "--cluster", "utecl1"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Member: evh2.aqd-unittest.ms.com [node_index: 0]",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRebindESXCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
