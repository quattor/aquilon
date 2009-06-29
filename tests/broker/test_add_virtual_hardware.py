#!/usr/bin/env python2.5
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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
                            "--cluster", "utecl1", "--cluster_type", "esx",
                            "--model", "utmedium"])

    def test_100_addinterfaces(self):
        for i in range(1, 10):
            self.noouttest(["add", "interface", "--machine", "evm%s" % i,
                            "--interface", "eth0", "--automac"])

    def test_500_verifyaddmachines(self):
        for i in range(1, 10):
            command = "show machine --machine evm%s" % i
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, "Virtual_machine: evm%s" % i, command)
            self.matchoutput(out, "Provided by esx cluster: utecl1", command)
            self.matchoutput(out, "Building: ut", command)
            self.matchoutput(out, "Vendor: utvendor Model: utmedium", command)
            self.matchoutput(out, "Cpu: Cpu xeon_2500 x 1", command)
            self.matchoutput(out, "Memory: 8192 MB", command)
            self.matchoutput(out,
                             "Interface: eth0 00:50:56:01:00:%02x boot=True" %
                             (i - 1),
                             command)

    def test_500_verifycatmachines(self):
        for i in range(1, 10):
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

    # FIXME: Test that cluster plenaries were updated correctly.

    # FIXME: Missing a test for add_interface non-esx automac.  (Might not
    # be possible to test with the current command set.)
    # FIXME: Missing a set of tests for add_interface to exercise the
    # automac algorithm.

    # FIXME: Missing a test for add_machine for a cluster without cluster_type.
    # (May not be possible with the aq client.)

    # Can't test this as there is no way to add a cluster without
    # an archetype of vmhost - yet.
#   def testfailaddnonvirtualcluster(self):
#       command = ["add", "machine", "--machine", "ut9s03p51",
#                  "--cluster", "utecl1", "--cluster_type", "esx",
#                  "--model", "utmedium"]
#       out = self.badrequesttest(command)
#       self.matchoutput(out,
#                        "Can only add virtual machines to "
#                        "clusters with archetype vmhost.",
#                        command)

    def testfailaddmissingcluster(self):
        command = ["add_machine", "--machine=ut9s03p51",
                   "--cluster=cluster-does-not-exist", "--cluster_type=esx",
                   "--model=utmedium"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "esx cluster 'cluster-does-not-exist' not found",
                         command)

    # FIXME: Add a test for add_machine that tries to use a non vmhost cluster.
    # This may not be possible yet as only esx clusters can be created and aqdb
    # constrains them to be vmhost.

    # FIXME: Add a test for add_machine that tries to override the location
    # of the cluster.

    # FIXME: Add a test that tries to add a virtual_machine without attaching
    # it to a cluster.

    # FIXME: Add tests for update_machine.  (Or is that UpdateVirtualHardware?)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddVirtualHardware)
    unittest.TextTestRunner(verbosity=2).run(suite)

