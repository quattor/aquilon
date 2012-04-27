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
"""Module for testing the vulcan2 related commands."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand

class TestVulcan20(TestBrokerCommand):

    def test_000_addutmc8(self):
        command = ["add_metacluster", "--metacluster=utmc8",
                   "--personality=metacluster", "--archetype=metacluster",
                   "--domain=unittest", "--building=ut", "--domain=unittest"]

        self.noouttest(command)

    def test_001_add_rg_to_cluster(self):
        command = ["add_resourcegroup", "--resourcegroup=utmc8as1",
                   "--cluster=utmc8", "--required_type=share"]
        self.successtest(command)

        command = ["show_resourcegroup", "--cluster=utmc8"]
        out = self.commandtest(command)
        self.matchoutput(out, "Resource Group: utmc8as1", command)
        self.matchoutput(out, "Bound to: ESX Metacluster utmc8", command)

        command = ["add_resourcegroup", "--resourcegroup=utmc8as2",
                   "--cluster=utmc8", "--required_type=share"]
        self.successtest(command)

        command = ["show_resourcegroup", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Resource Group: utmc8as1", command)
        self.matchoutput(out, "Resource Group: utmc8as2", command)

    def test_002_cat_cluster(self):
        command = ["cat", "--cluster", "utmc8"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "'/system/resources/resourcegroup' = "
                         "push(create(\"resource/cluster/utmc8/resourcegroup"
                         "/utmc8as1/config\"));",
                         command)


    def test_003_add_share_to_rg(self):
        command = ["add_share", "--resourcegroup=utmc8as1",
                   "--cluster=utmc8", "--share=test_v2_share",
                   "--latency=5"]
        self.successtest(command)

        command = ["show_share", "--resourcegroup=utmc8as1",
                   "--cluster=utmc8", "--share=test_v2_share"]
        out = self.commandtest(command)
        self.matchoutput(out, "Share: test_v2_share", command)
        self.matchoutput(out, "Bound to: Resource Group utmc8as1", command)
        self.matchoutput(out, "Latency: 5", command)

        command = ["add_share", "--resourcegroup=utmc8as2",
                   "--cluster=utmc8", "--share=test_v2_share",
                   "--latency=5"]
        self.successtest(command)

        command = ["show_share", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Share: test_v2_share", command)
        self.matchoutput(out, "Bound to: Resource Group utmc8as1", command)
        self.matchoutput(out, "Bound to: Resource Group utmc8as2", command)

    def test_003_add_same_share_name_fail(self):
        command = ["add_share", "--resourcegroup=utmc8as1",
                   "--metacluster=utmc8", "--share=test_v2_share",
                   "--latency=5"]
        err = self.badrequesttest(command)
        self.matchoutput(err, "Bad Request: Share test_v2_share, "
                         "bundleresource instance already exists.", command)

    def test_004_cat_rg(self):
        command = ["cat", "--resourcegroup=utmc8as1", "--cluster=utmc8",
                   "--generate"]
        out = self.commandtest(command)
        self.matchoutput(out, "structure template resource/cluster/utmc8/"
                         "resourcegroup/utmc8as1/config;",
                         command)
        self.matchoutput(out, '"name" = "utmc8as1', command)
        self.matchoutput(out,
                         '"resources/share" = '
                         'push(create("resource/cluster/utmc8/resourcegroup/'
                         'utmc8as1/share/test_v2_share/config"));',
                         command)

        # TODO no resources, waiting for big resource branch

    def test_005_cat_share(self):
        command = ["cat", "--share=test_v2_share", "--resourcegroup=utmc8as1",
                   "--cluster=utmc8", "--generate"]
        out = self.commandtest(command)
        self.matchoutput(out, "structure template resource/cluster/utmc8/"
                         "resourcegroup/utmc8as1/share/test_v2_share/config;",
                         command)
        self.matchoutput(out, '"sharename" = "test_v2_share";', command)
        self.matchoutput(out, '"server" = "lnn30f1";', command)
        self.matchoutput(out, '"mountpoint" = "/vol/lnn30f1v1/test_v2_share";',
                         command)
        self.matchoutput(out, '"latency" = 5;', command)

    def test_010_addfilesystemfail(self):
        command = ["add_filesystem", "--filesystem=fs1", "--type=ext3",
                   "--mountpoint=/mnt", "--blockdevice=/dev/foo/bar",
                   "--bootmount",
                   "--dumpfreq=1", "--fsckpass=3", "--options=ro",
                   "--comments=testing",
                   "--resourcegroup=utmc8as1"]
        err = self.badrequesttest(command)
        self.matchoutput(err, "Bad Request: Resource's filesystem type "
                         "differs from the requested share",
                         command)

    def test_011_verify_rg(self):
        command = ["show_resourcegroup", "--cluster=utmc8"]
        out = self.commandtest(command)
        self.matchoutput(out, "Resource Group: utmc8as1", command)
        self.matchoutput(out, "Share: test_v2_share", command)

    def test_012_verifyutmc8(self):
        command = "show metacluster --metacluster utmc8"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Share: test_v2_share", command)

    # TODO renumber
    def test_104_delresourcegroup(self):
        command = ["del_share", "--resourcegroup=utmc8as1",
                   "--cluster=utmc8", "--share=test_v2_share"]
        self.successtest(command)

        command = ["del_resourcegroup", "--resourcegroup=utmc8as1",
                   "--cluster=utmc8"]
        self.successtest(command)

        command = ["del_share", "--resourcegroup=utmc8as2",
                   "--cluster=utmc8", "--share=test_v2_share"]
        self.successtest(command)

        command = ["del_resourcegroup", "--resourcegroup=utmc8as2",
                   "--cluster=utmc8"]
        self.successtest(command)

    def test_105_delutmc8(self):
        command = ["del_metacluster", "--metacluster=utmc8"]
        self.noouttest(command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestVulcan20)
    unittest.TextTestRunner(verbosity=2).run(suite)
