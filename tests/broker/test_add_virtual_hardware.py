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

    def test_000_addevm1(self):
        self.noouttest(["add", "machine", "--machine", "evm1",
                        "--cluster", "utecl1", "--cluster_type", "esx",
                        "--model", "utmedium"])

    def test_100_addevm1interface(self):
        self.noouttest(["add", "interface", "--machine", "evm1",
                        "--interface", "eth0", "--automac"])

    def test_500_verifyaddevm1(self):
        command = "show machine --machine evm1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Virtual_machine: evm1", command)
        self.matchoutput(out, "Provided by esx cluster: utecl1", command)
        self.matchoutput(out, "Building: ut", command)
        self.matchoutput(out, "Vendor: utvendor Model: utmedium", command)
        self.matchoutput(out, "Cpu: Cpu xeon_2500 x 1", command)
        self.matchoutput(out, "Memory: 8192 MB", command)
        self.matchoutput(out, "Interface: eth0 00:50:56:01:00:00 boot=True",
                         command)

    # FIXME: Make sure any necessary cluster info appears here.
    def test_500_verifycatevm1(self):
        command = "cat --machine evm1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
            """"location" = "ut.ny.na";""",
            command)
        self.matchoutput(out,
            """include { 'hardware/machine/utvendor/utmedium' };""",
            command)
        self.matchoutput(out,
            """"ram" = list(create("hardware/ram/generic", "size", 8192*MB));""",
            command)
        self.matchoutput(out,
            """"cpu" = list(create("hardware/cpu/intel/xeon_2500"));""",
            command)
        self.matchoutput(out,
                         """"cards/nic/eth0/hwaddr" = "00:50:56:01:00:00";""",
                         command)
        self.matchoutput(out, """"cards/nic/eth0/boot" = true;""", command)

    # FIXME: Test that cluster plenaries were updated correctly.


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddVirtualHardware)
    unittest.TextTestRunner(verbosity=2).run(suite)

