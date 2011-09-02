#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011  Contributor
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
"""Module for testing the del cluster command."""

import os
import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelCluster(TestBrokerCommand):

    def test_100_delutgrid1(self):
        command = ["del_cluster", "--cluster=utgrid1"]
        self.successtest(command)

    def test_100_verifydelutgrid1(self):
        command = ["show_cluster", "--cluster=utgrid1"]
        self.notfoundtest(command)

    def test_100_verifyall(self):
        command = ["show_cluster", "--all"]
        out = self.commandtest(command)
        self.matchclean(out, "Grid Cluster: utgrid", command)

    def test_100_delnotfound(self):
        command = ["del_cluster", "--cluster=grid_cluster-does-not-exist"]
        self.notfoundtest(command)

    def test_100_verifyplenaryclusterclient(self):
        plenary = os.path.join(self.config.get("broker", "plenarydir"),
                               "cluster", "utgrid1", "client.tpl")
        self.failIf(os.path.exists(plenary),
                    "Plenary file '%s' still exists" % plenary)
        plenary = os.path.join(self.config.get("broker", "builddir"),
                               "domains", "unittest", "profiles",
                               "clusters", "utgrid1.tpl")
        self.failIf(os.path.exists(plenary),
                    "Plenary file '%s' still exists" % plenary)

    def test_200_delutvcs1(self):
        command = ["del_cluster", "--cluster=utvcs1"]
        self.successtest(command)

    def test_200_verifydelutvcs1(self):
        command = ["show_cluster", "--cluster=utvcs1"]
        self.notfoundtest(command)

    def test_200_verifyall(self):
        command = ["show_cluster", "--all"]
        out = self.commandtest(command)
        self.matchclean(out, "HA Cluster: utvcs", command)

    def test_300_delutstorage1(self):
        command = ["del_cluster", "--cluster=utstorage1"]
        self.successtest(command)

    def test_300_verifydelutstorage1(self):
        command = ["show_cluster", "--cluster=utstorage1"]
        self.notfoundtest(command)

    def test_300_delutstorage2(self):
        command = ["del_cluster", "--cluster=utstorage2"]
        self.successtest(command)

    def test_300_verifydelutstorage2(self):
        command = ["show_cluster", "--cluster=utstorage2"]
        self.notfoundtest(command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
