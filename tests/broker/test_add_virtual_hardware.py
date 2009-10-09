#!/usr/bin/env python2.5
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009  Contributor
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
"""Module for testing commands that add virtual hardware."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestAddVirtualHardware(TestBrokerCommand):

    def test_000_addmachines(self):
        for i in range(1, 10):
            self.noouttest(["add", "machine", "--machine", "evm%s" % i,
                            "--cluster", "utecl1", "--model", "utmedium"])

    def test_010_failwithoutcluster(self):
        command = ["add_machine", "--machine=evm999", "--rack=ut3",
                   "--model=utmedium"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Virtual machines must be assigned to a cluster.",
                         command)

    # The current client does not allow this test.
#   def test_010_failbadlocation(self):
#       command = ["add_machine", "--machine=evm999", "--rack=np997",
#                  "--model=utmedium", "--cluster=utecl1"]
#       out = self.badrequesttest(command)
#       self.matchoutput(out,
#                        "Cannot override cluster location building ut "
#                        "with location rack np997",
#                        command)

    # Replacement for the test above.
    def test_010_failbadlocation(self):
        command = ["add_machine", "--machine=evm999", "--rack=np997",
                   "--model=utmedium", "--cluster=utecl1"]
        out = self.badoptiontest(command)
        self.matchoutput(out, "cluster conflicts with rack", command)

    def test_090_verifyaddmachines(self):
        command = ["show_esx_cluster", "--cluster=utecl1"]
        out = self.commandtest(command)
        self.matchoutput(out, "esx cluster: utecl1", command)
        self.matchoutput(out, "Virtual Machine count: 9", command)

    def test_100_addinterfaces(self):
        for i in range(1, 8):
            self.noouttest(["add", "interface", "--machine", "evm%s" % i,
                            "--interface", "eth0", "--automac"])

    def test_110_addinterfaces(self):
        self.noouttest(["add", "interface", "--machine", "evm9",
                        "--interface", "eth0", "--mac", "00:50:56:3f:ff:ff"])

    def test_120_addinterfaces(self):
        # This should now fill in the 'hole' between 7 and 9
        self.noouttest(["add", "interface", "--machine", "evm8",
                        "--interface", "eth0", "--automac"])

    def test_130_adddisks(self):
        # The first 8 shares should work...
        for i in range(1, 9):
            self.noouttest(["add", "disk", "--machine", "evm%s" % i,
                            "--disk", "sda", "--type", "sata",
                            "--capacity", "15", "--share", "test_share_%s" % i,
                            "--address", "0:0"])

    def test_150_failaddillegaldisk(self):
        command = ["add", "disk", "--machine", "evm9", "--disk", "sda",
                   "--type", "sata", "--capacity", "15",
                   "--share", "test_share_9", "--address", "badaddress"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "disk address 'badaddress' is illegal", command)

    def test_160_failaddmaxshares(self):
        # Number 9 should trip the limit.
        command = ["add", "disk", "--machine", "evm9", "--disk", "sda",
                   "--type", "sata", "--capacity", "15",
                   "--share", "test_share_9", "--address", "0:0"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "would exceed the metacluster's max_shares",
                         command)

    def test_190_verifyadddisk(self):
        command = ["show_metacluster", "--metacluster=namc1"]
        out = self.commandtest(command)
        self.matchoutput(out, "MetaCluster: namc1", command)
        for i in range(1, 9):
            self.matchoutput(out, "Share: test_share_%s" % i, command)
        self.matchclean(out, "Share: test_share_9", command)

    def test_200_updatemachine(self):
        self.noouttest(["update_machine", "--machine", "evm9",
                        "--cluster", "utecl2"])
        oldpath = os.path.join(self.config.get("broker", "plenarydir"),
                               "machine", "americas", "ut", "ut10", "evm9.tpl")
        newpath = os.path.join(self.config.get("broker", "plenarydir"),
                               "machine", "americas", "ut", "None", "evm9.tpl")
        self.failIf(os.path.exists(oldpath),
                    "Plenary file '%s' not removed." % oldpath)
        self.failUnless(os.path.exists(newpath),
                        "Plenary file '%s' not created." % newpath)

    def test_300_failrebindhost(self):
        command = ["rebind_esx_cluster", "--cluster=utecl1",
                   "--host=evh1.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "would exceed vm_to_host_ratio", command)

    def test_310_failrebindmachine(self):
        command = ["update_machine", "--machine", "evm1",
                   "--cluster", "utecl2"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "would exceed vm_to_host_ratio", command)

    def test_500_verifyaddmachines(self):
        # Skipping evm9 since the mac is out of sequence and different cluster
        for i in range(1, 9):
            command = "show machine --machine evm%s" % i
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, "Virtual_machine: evm%s" % i, command)
            self.matchoutput(out, "Hosted by esx cluster: utecl1", command)
            self.matchoutput(out, "Building: ut", command)
            self.matchoutput(out, "Vendor: utvendor Model: utmedium", command)
            self.matchoutput(out, "Cpu: Cpu xeon_2500 x 1", command)
            self.matchoutput(out, "Memory: 8192 MB", command)
            self.matchoutput(out,
                             "Interface: eth0 00:50:56:01:00:%02x boot=True" %
                             (i - 1),
                             command)

    def test_500_verifycatmachines(self):
        # Skipping evm9 since the mac is out of sequence
        for i in range(1, 9):
            command = "cat --machine evm%s" % i
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, """"location" = "ut.ny.na";""", command)
            self.matchoutput(out,
                             """include { """
                             """'hardware/machine/utvendor/utmedium' };""",
                             command)
            self.matchoutput(out,
                             """"ram" = list(create("hardware/ram/generic", """
                             """"size", 8192*MB));""",
                             command)
            self.matchoutput(out,
                             """"cpu" = list(create("""
                             """"hardware/cpu/intel/xeon_2500"));""",
                             command)
            self.matchoutput(out,
                             """"cards/nic/eth0/hwaddr" """
                             """= "00:50:56:01:00:%02x";""" % (i - 1),
                             command)
            self.matchoutput(out, """"cards/nic/eth0/boot" = true;""", command)

    # FIXME: Add a test for creating an aquilon host out of a virtual
    # machine.

    def test_500_verifycatcluster(self):
        command = "cat --cluster=utecl1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "object template clusters/utecl1;", command)
        self.matchoutput(out, "'/system/cluster/name' = 'utecl1';", command)
        self.matchoutput(out, "'/system/metacluster/name' = 'namc1';", command)
        self.matchoutput(out, "'/system/cluster/machines' = nlist(", command)
        for i in range(1, 9):
            machine = "evm%s" % i
            self.matchoutput(out,
                             "'%s', create('machine/americas/ut/None/%s')," %
                             (machine, machine),
                             command)
        self.matchclean(out, "'evm9', create('machine/americas/ut/None/evm9'),",
                        command)
        self.searchoutput(out,
                          r"include { 'service/esx_management/ut.[ab]/"
                          r"client/config' };",
                          command)

    def test_600_makecluster(self):
        command = ["make_cluster", "--cluster=utecl1"]
        (out, err) = self.successtest(command)

    def test_700_add_windows(self):
        command = ["add_windows_host", "--hostname=aqddesk1.msad.ms.com",
                   "--machine=evm1", "--comments=Windows Virtual Desktop"]
        self.noouttest(command)

    def test_800_verify_windows(self):
        command = "show host --hostname aqddesk1.msad.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hostname: aqddesk1.msad.ms.com", command)
        self.matchoutput(out, "Virtual_machine: evm1", command)
        self.matchoutput(out, "Comments: Windows Virtual Desktop", command)

    # FIXME: Missing a test for add_interface non-esx automac.  (Might not
    # be possible to test with the current command set.)

    # Can't test this as there is no way to add a cluster without
    # an archetype of vmhost - yet.
#   def testfailaddnonvirtualcluster(self):
#       command = ["add", "machine", "--machine", "ut9s03p51",
#                  "--cluster", "utecl1", "--model", "utmedium"]
#       out = self.badrequesttest(command)
#       self.matchoutput(out,
#                        "Can only add virtual machines to "
#                        "clusters with archetype vmhost.",
#                        command)

    def testfailaddmissingcluster(self):
        command = ["add_machine", "--machine=ut9s03p51",
                   "--cluster=cluster-does-not-exist", "--model=utmedium"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Cluster 'cluster-does-not-exist' not found",
                         command)

    # FIXME: Add a test for add_machine that tries to use a non vmhost cluster.
    # This may not be possible yet as only esx clusters can be created and aqdb
    # constrains them to be vmhost.

    def testfailaddnonvirtual(self):
        command = ["add_machine", "--machine=ut3c1n1", "--model=utmedium",
                   "--chassis=ut3c1.aqd-unittest.ms.com", "--slot=1"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Virtual machines must be assigned to a cluster.",
                         command)

    def testfailaddnoncluster(self):
        command = ["add_machine", "--machine=ut3c1n1", "--cluster=utecl1",
                   "--model=hs21-8853l5u"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Only virtual machines can have a cluster attribute.",
                         command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddVirtualHardware)
    unittest.TextTestRunner(verbosity=2).run(suite)

