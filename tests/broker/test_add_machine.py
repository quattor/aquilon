#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
"""Module for testing the add machine command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.6"))

from brokertest import TestBrokerCommand


class TestAddMachine(TestBrokerCommand):

    def testaddut3c5n10(self):
        self.noouttest(["add", "machine", "--machine", "ut3c5n10",
            "--rack", "ut3", "--model", "hs21-8853l5u", "--cpucount", "2",
            "--cpuvendor", "intel", "--cpuname", "xeon", "--cpuspeed", "2660",
            "--memory", "8192", "--serial", "99C5553"])

    def testverifyaddut3c5n10(self):
        command = "show machine --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut3c5n10", command)
        self.matchoutput(out, "Rack: ut3", command)
        self.matchoutput(out, "Vendor: ibm Model: hs21-8853l5u", command)
        self.matchoutput(out, "Cpu: Cpu xeon_2660 x 2", command)
        self.matchoutput(out, "Memory: 8192 MB", command)
        self.matchoutput(out, "Serial: 99C5553", command)

    def testverifydelmodel(self):
        # This should be in test_del_model.py but when that is run there are no
        # more machines defined...
        command = "del model --model hs21-8853l5u --vendor ibm"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Model hs21-8853l5u is still in use and cannot "
                         "be deleted.", command)

    def testverifycatut3c5n10(self):
        command = "cat --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
            """"location" = "ut.ny.na";""",
            command)
        self.matchoutput(out,
            """"serialnumber" = "99C5553";""",
            command)
        self.matchoutput(out,
            """"sysloc/dns_search_domains" = list("new-york.ms.com");""",
            command)
        self.matchoutput(out,
            """include { 'hardware/machine/ibm/hs21-8853l5u' };""",
            command)
        self.matchoutput(out,
            """"ram" = list(create("hardware/ram/generic", "size", 8192*MB));""",
            command)
        # 1st cpu
        self.matchoutput(out,
            """"cpu" = list(create("hardware/cpu/intel/xeon_2660"),""",
            command)
        # 2nd cpu
        self.matchoutput(out,
            """create("hardware/cpu/intel/xeon_2660"));""",
            command)

    def testaddut3c1n3(self):
        self.noouttest(["add", "machine", "--machine", "ut3c1n3",
            "--chassis", "ut3c1.aqd-unittest.ms.com", "--slot", "3",
            "--model", "hs21-8853l5u", "--cpucount", "2",
            "--cpuvendor", "intel", "--cpuname", "xeon", "--cpuspeed", "2660",
            "--memory", "8192", "--serial", "KPDZ406"])

    def testshowslot(self):
        command = "show machine --slot 3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut3c1n3", command)

    def testshowchassisslot(self):
        command = "show machine --chassis ut3c1.aqd-unittest.ms.com --slot 3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut3c1n3", command)

    def testverifyaddut3c1n3(self):
        command = "show machine --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut3c1n3", command)
        self.matchoutput(out, "Chassis: ut3c1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Slot: 3", command)
        self.matchoutput(out, "Vendor: ibm Model: hs21-8853l5u", command)
        self.matchoutput(out, "Cpu: Cpu xeon_2660 x 2", command)
        self.matchoutput(out, "Memory: 8192 MB", command)
        self.matchoutput(out, "Serial: KPDZ406", command)

    def testverifycatut3c1n3(self):
        command = "cat --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
            """"location" = "ut.ny.na";""",
            command)
        self.matchoutput(out,
            """"serialnumber" = "KPDZ406";""",
            command)
        self.matchoutput(out,
            """include { 'hardware/machine/ibm/hs21-8853l5u' };""",
            command)
        self.matchoutput(out,
            """"ram" = list(create("hardware/ram/generic", "size", 8192*MB));""",
            command)
        # 1st cpu
        self.matchoutput(out,
            """"cpu" = list(create("hardware/cpu/intel/xeon_2660"),""",
            command)
        # 2nd cpu
        self.matchoutput(out,
            """create("hardware/cpu/intel/xeon_2660"));""",
            command)

    def testaddut3c1n4(self):
        self.noouttest(["add", "machine", "--machine", "ut3c1n4",
            "--rack", "ut3", "--model", "hs21-8853l5u", "--serial", "KPDZ407"])

    def testverifyaddut3c1n4(self):
        command = "show machine --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut3c1n4", command)
        self.matchoutput(out, "Rack: ut3", command)
        self.matchoutput(out, "Vendor: ibm Model: hs21-8853l5u", command)
        self.matchoutput(out, "Cpu: Cpu xeon_2660 x 2", command)
        self.matchoutput(out, "Memory: 8192 MB", command)
        self.matchoutput(out, "Serial: KPDZ407", command)

    def testverifycatut3c1n4(self):
        command = "cat --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
            """"location" = "ut.ny.na";""",
            command)
        self.matchoutput(out,
            """"serialnumber" = "KPDZ407";""",
            command)
        self.matchoutput(out,
            """include { 'hardware/machine/ibm/hs21-8853l5u' };""",
            command)
        self.matchoutput(out,
            """"ram" = list(create("hardware/ram/generic", "size", 8192*MB));""",
            command)
        # 1st cpu
        self.matchoutput(out,
            """"cpu" = list(create("hardware/cpu/intel/xeon_2660"),""",
            command)
        # 2nd cpu
        self.matchoutput(out,
            """create("hardware/cpu/intel/xeon_2660"));""",
            command)

    # Testing that add machine does not allow a tor_switch....
    def testrejectut3gd2r01(self):
        self.badrequesttest(["add", "machine", "--machine", "ut3gd2r01",
            "--rack", "ut3", "--model", "uttorswitch"])

    def testverifyrejectut3gd2r01(self):
        command = "show machine --machine ut3gd2r01"
        out = self.notfoundtest(command.split(" "))

    # Testing that an invalid cpu returns an error (not an internal error)...
    # (There should be no cpu with speed==2 in the database)
    def testrejectut3c1n5(self):
        self.badrequesttest(["add", "machine", "--machine", "ut3c1n5",
            "--rack", "ut3", "--model", "hs21-8853l5u", "--cpucount", "2",
            "--cpuvendor", "intel", "--cpuname", "xeon", "--cpuspeed", "2",
            "--memory", "8192", "--serial", "KPDZ406"])

    def testverifyrejectut3c1n5(self):
        command = "show machine --machine ut3c1n5"
        out = self.notfoundtest(command.split(" "))

    def testrejectmissingmemory(self):
        command = ["add", "machine", "--machine", "ut3c1n6",
            "--rack", "ut3", "--model", "utblade", "--cpucount", "2",
            "--cpuvendor", "intel", "--cpuname", "xeon", "--cpuspeed", "2660",
            "--serial", "AAAAAAA"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "does not have machine specification defaults, please specify --memory",
                         command)

    def testverifyrejectmissingmemory(self):
        command = "show machine --machine ut3c1n6"
        out = self.notfoundtest(command.split(" "))

    def testrejectmissingmodel(self):
        command = ["add", "machine", "--machine", "ut3c1n7",
            "--rack", "ut3", "--model", "utblade", "--serial", "BBBBBBB"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "does not have machine specification defaults",
                         command)

    def testverifyrejectmissingmodel(self):
        command = "show machine --machine ut3c1n7"
        out = self.notfoundtest(command.split(" "))

    # When doing an end-to-end test, these two entries should be
    # created as part of a sweep of a Dell rack.  They represent
    # two mac addresses seen on the same port, only one of which
    # is actually a host.  The other is a management interface.
    def testaddut3s01p1a(self):
        self.noouttest(["add", "machine", "--machine", "ut3s01p1a",
            "--rack", "ut3", "--model", "poweredge_6650"])

    def testverifyaddut3s01p1a(self):
        command = "show machine --machine ut3s01p1a"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Rackmount: ut3s01p1a", command)

    def testaddut3s01p1b(self):
        self.noouttest(["add", "machine", "--machine", "ut3s01p1b",
            "--rack", "ut3", "--model", "poweredge_6650"])

    def testverifyaddut3s01p1b(self):
        command = "show machine --machine ut3s01p1b"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Rackmount: ut3s01p1b", command)

    # When doing an end-to-end test, these entries should be
    # created as part of a sweep of a Verari rack
    # (ut01ga1s02.aqd-unittest.ms.com).
    def testaddut8s02p1(self):
        self.noouttest(["add", "machine", "--machine", "ut8s02p1",
            "--rack", "ut8", "--model", "vb1205xm"])

    def testverifyaddut8s02p1(self):
        command = "show machine --machine ut8s02p1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut8s02p1", command)

    def testaddut8s02p2(self):
        self.noouttest(["add", "machine", "--machine", "ut8s02p2",
            "--rack", "ut8", "--model", "vb1205xm"])

    def testverifyaddut8s02p2(self):
        command = "show machine --machine ut8s02p2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut8s02p2", command)

    def testaddut8s02p3(self):
        self.noouttest(["add", "machine", "--machine", "ut8s02p3",
            "--rack", "ut8", "--model", "vb1205xm"])

    def testverifyaddut8s02p3(self):
        command = "show machine --machine ut8s02p3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut8s02p3", command)

    # one-offs for testing odd add host parameter combinations for
    # archetypes aurora and windows for increased code coverage
    def testaddut8s02p4(self):
        self.noouttest(["add", "machine", "--machine", "ut8s02p4",
            "--rack", "ut8", "--model", "vb1205xm"])

    def testverifyaddut8s02p4(self):
        command = "show machine --machine ut8s02p4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut8s02p4", command)

    def testaddut8s02p5(self):
        self.noouttest(["add", "machine", "--machine", "ut8s02p5",
            "--rack", "ut8", "--model", "vb1205xm"])

    def testverifyaddut8s02p5(self):
        command = "show machine --machine ut8s02p5"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut8s02p5", command)


    # This test should look very different, but these were needed for
    # testing chassis updates...
    def testaddhprack(self):
        # number 50 is in use by the tor_switch.
        for i in range(51, 100):
            port = i - 50
            self.noouttest(["add", "machine", "--machine", "ut9s03p%d" % port,
                            "--rack", "ut9", "--model", "bl260c"])

    def testverifyaddhprack(self):
        for i in range(51, 100):
            port = i - 50
            command = "show machine --machine ut9s03p%d" % port
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, "Blade: ut9s03p%d" % port, command)

    def testaddverarirack(self):
        # number 100 is in use by the tor_switch.
        for i in range(101, 150):
            port = i - 100
            self.noouttest(["add", "machine", "--machine", "ut10s04p%d" % port,
                            "--rack", "ut10", "--model", "vb1205xm"])

    def testadd10gigracks(self):
        for port in range(1, 13):
            self.noouttest(["add", "machine", "--machine", "ut11s01p%d" % port,
                            "--rack", "ut11", "--model", "vb1205xm"])
            self.noouttest(["add", "machine", "--machine", "ut12s02p%d" % port,
                            "--rack", "ut12", "--model", "vb1205xm"])

    # FIXME: Missing a test for adding a macihne to a chassis where the
    # fqdn given for the chassis isn't *actually* a chassis.
    # FIXME: Missing a test for chassis without a slot.  (May not be possible
    # with the aq client.)
    # FIXME: Missing a test for a location that conflicts with chassis loc.
    # FIXME: Missing a test for a slot without a chassis.  (May not be possible
    # with the aq client.)
    # FIXME: Add a test where the machine trying to be created already exists.

    # Note: More regression tests are in the test_add_virtual_hardware module.


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddMachine)
    unittest.TextTestRunner(verbosity=2).run(suite)
