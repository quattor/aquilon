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
"""Module for testing the add resourcegroup command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddResourceGroup(TestBrokerCommand):

    def test_00_add_rg_to_cluster(self):
        command = ["add_resourcegroup", "--resourcegroup=utvcs1as1",
                   "--cluster=utvcs1"]
        self.successtest(command)

        command = ["show_resourcegroup", "--cluster=utvcs1"]
        out = self.commandtest(command)
        self.matchoutput(out, "ResourceGroup: utvcs1as1", command)
        self.matchoutput(out,
                         "Bound to: High Availability Cluster utvcs1",
                         command)

        command = ["show_resourcegroup", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "ResourceGroup: utvcs1as1", command)

    def test_add_fs_to_rg(self):
        command = ["add_filesystem", "--filesystem=fs1", "--type=ext3",
                   "--mountpoint=/mnt", "--blockdevice=/dev/foo/bar",
                   "--bootmount",
                   "--dumpfreq=1", "--fsckpass=3", "--options=ro",
                   "--comments=testing",
                   "--resourcegroup=utvcs1as1"]
        self.successtest(command)

        command = ["show_filesystem", "--filesystem=fs1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Filesystem: fs1", command)
        self.matchoutput(out, "Bound to: ResourceGroup utvcs1as1", command)
        self.matchoutput(out, "Block Device: /dev/foo/bar", command)
        self.matchoutput(out, "Mount at boot: True", command)
        self.matchoutput(out, "Mountopts: ro", command)
        self.matchoutput(out, "Mountpoint: /mnt", command)
        self.matchoutput(out, "Dump Freq: 1", command)
        self.matchoutput(out, "Fsck Pass: 3", command)
        self.matchoutput(out, "Comments: testing", command)

    def test_del_resourcegroup(self):
        command = ["del_resourcegroup", "--resourcegroup=utvcs1as1"]
        self.successtest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddResourceGroup)
    unittest.TextTestRunner(verbosity=2).run(suite)
