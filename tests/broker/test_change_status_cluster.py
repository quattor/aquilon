#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010,2011,2012  Contributor
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
"""Module for testing the cluster status commands."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.6"))

from brokertest import TestBrokerCommand


class TestChangeClusterStatus(TestBrokerCommand):

    # This class is invoked after test_bind_esx_cluster, so we
    # know that we have a cluster (utecl1) which has 5 member hosts,
    # each of which are in "build" status.
    def test_100_BlockPromotion(self):
        self.successtest(["change_status",
                          "--hostname", "evh1.aqd-unittest.ms.com",
                          "--buildstatus", "ready"])

        command = "show host --hostname evh1.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))

        self.matchoutput(out, "Build Status: almostready", command)

    def test_110_PromoteCluster(self):
        self.successtest(["change_status", "--cluster", "utecl1",
                          "--buildstatus", "ready"])

        # the almostready host should now be promoted
        command = "show host --hostname evh1.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Build Status: ready", command)

        # the build host should be unchanged
        command = "show host --hostname evh2.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Build Status: build", command)


    def test_120_BindDemotion(self):
        self.successtest(["cluster",
                          "--hostname", "evh1.aqd-unittest.ms.com",
                          "--cluster", "utecl2"])

        command = "show host --hostname evh1.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Build Status: almostready", command)

        # Put the host back and confirm it can move to ready
        self.successtest(["cluster",
                          "--hostname", "evh1.aqd-unittest.ms.com",
                          "--cluster", "utecl1"])
        self.successtest(["change_status",
                          "--hostname", "evh1.aqd-unittest.ms.com",
                          "--buildstatus", "ready"])

        command = "show host --hostname evh1.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))

        self.matchoutput(out, "Build Status: ready", command)

    def test_130_DemoteCluster(self):
        self.successtest(["change_status", "--cluster", "utecl1",
                          "--buildstatus", "rebuild"])

        # the ready host should be demoted
        command = "show host --hostname evh1.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Build Status: almostready", command)

        # the build host should be unchanged
        command = "show host --hostname evh2.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Build Status: build", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestChangeClusterStatus)
    unittest.TextTestRunner(verbosity=2).run(suite)

