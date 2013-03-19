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
"""Module for testing the add machine command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddMachine(TestBrokerCommand):

    def testaddut3c5n10(self):
        self.noouttest(["add", "machine", "--machine", "ut3c5n10",
                        "--rack", "ut3", "--model", "hs21-8853l5u",
                        "--cpucount", "2", "--cpuvendor", "intel",
                        "--cpuname", "xeon", "--cpuspeed", "2660",
                        "--memory", "8192", "--serial", "99C5553",
                        "--comments", "Some machine comments"])

    def testverifyaddut3c5n10(self):
        command = "show machine --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut3c5n10", command)
        self.matchoutput(out, "Rack: ut3", command)
        self.matchoutput(out, "Vendor: ibm Model: hs21-8853l5u", command)
        self.matchoutput(out, "Cpu: xeon_2660 x 2", command)
        self.matchoutput(out, "Memory: 8192 MB", command)
        self.matchoutput(out, "Serial: 99C5553", command)
        self.matchoutput(out, "Comments: Some machine comments", command)
        self.matchclean(out, "Primary Name:", command)

    # Copy of ut3c5n10, for network based service mappings
    def testaddut3c5n11(self):
        self.noouttest(["add", "machine", "--machine", "ut3c5n11",
                        "--rack", "ut3", "--model", "hs21-8853l5u",
                        "--cpucount", "2", "--cpuvendor", "intel",
                        "--cpuname", "xeon", "--cpuspeed", "2660",
                        "--memory", "8192", "--serial", "99C5553",
                        "--comments", "For network based service mappings"])

    # Copy of ut3c5n10, for network based service mappings
    def testaddut3c5n12(self):
        self.noouttest(["add", "machine", "--machine", "ut3c5n12",
                        "--rack", "ut3", "--model", "hs21-8853l5u",
                        "--cpucount", "2", "--cpuvendor", "intel",
                        "--cpuname", "xeon", "--cpuspeed", "2660",
                        "--memory", "8192", "--serial", "99C5553",
                        "--comments", "For net/pers based service mappings"])

    def testverifyaddut3c5n11(self):
        command = "show machine --machine ut3c5n11"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut3c5n11", command)
        self.matchoutput(out, "Rack: ut3", command)
        self.matchoutput(out, "Vendor: ibm Model: hs21-8853l5u", command)
        self.matchoutput(out, "Cpu: xeon_2660 x 2", command)
        self.matchoutput(out, "Memory: 8192 MB", command)
        self.matchoutput(out, "Serial: 99C5553", command)
        self.matchoutput(out, "Comments: For network based service mappings",
                         command)
        self.matchclean(out, "Primary Name:", command)

    def testverifydelmodel(self):
        # This should be in test_del_model.py but when that is run there are no
        # more machines defined...
        command = "del model --model hs21-8853l5u --vendor ibm"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Model ibm/hs21-8853l5u is still in use and "
                         "cannot be deleted.", command)

    def testverifycatut3c5n10(self):
        command = "cat --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"location" = "ut.ny.na";', command)
        self.matchoutput(out, '"serialnumber" = "99C5553";', command)
        # DNS maps:
        # - aqd-unittest.ms.com comes from rack ut3
        # - utroom1 also has aqd-unittest.ms.com mapped _after_ td1 and td2,
        #   but the rack mapping is more specific, so aqd-unittest.ms.com
        #   remains at the beginning
        # - new-york.ms.com comes from the campus
        self.searchoutput(out,
                          r'"sysloc/dns_search_domains" = list\(\s*'
                          r'"aqd-unittest.ms.com",\s*'
                          r'"td1.aqd-unittest.ms.com",\s*'
                          r'"td2.aqd-unittest.ms.com",\s*'
                          r'"new-york.ms.com"\s*\);',
                          command)
        self.matchoutput(out,
                         'include { "hardware/machine/ibm/hs21-8853l5u" };',
                         command)
        self.searchoutput(out,
                          r'"ram" = list\(\s*'
                          r'create\("hardware/ram/generic",\s*'
                          r'"size", 8192\*MB\s*\)\s*\);',
                          command)
        self.searchoutput(out,
                          r'"cpu" = list\(\s*'
                          r'create\("hardware/cpu/intel/xeon_2660"\),\s*'
                          r'create\("hardware/cpu/intel/xeon_2660"\s*\)\s*\);',
                          command)

    # Used for Zebra tests
    def testaddut3c5n2(self):
        self.noouttest(["add", "machine", "--machine", "ut3c5n2",
                        "--rack", "ut3", "--model", "hs21-8853l5u",
                        "--cpucount", "2", "--cpuvendor", "intel",
                        "--cpuname", "xeon", "--cpuspeed", "2660",
                        "--memory", "8192"])

    # Used for bonding tests
    def testaddut3c5n3(self):
        self.noouttest(["add", "machine", "--machine", "ut3c5n3",
                        "--rack", "ut3", "--model", "hs21-8853l5u",
                        "--cpucount", "2", "--cpuvendor", "intel",
                        "--cpuname", "xeon", "--cpuspeed", "2660",
                        "--memory", "8192"])

    # Used for bridge tests
    def testaddut3c5n4(self):
        self.noouttest(["add", "machine", "--machine", "ut3c5n4",
                        "--rack", "ut3", "--model", "hs21-8853l5u",
                        "--cpucount", "2", "--cpuvendor", "intel",
                        "--cpuname", "xeon", "--cpuspeed", "2660",
                        "--memory", "8192"])

    # Used for house-of-cards location testing
    def testaddjack(self):
        self.noouttest(["add", "machine", "--machine", "jack",
                        "--rack", "cards1", "--model", "hs21-8853l5u",
                        "--cpucount", "2", "--cpuvendor", "intel",
                        "--cpuname", "xeon", "--cpuspeed", "2660",
                        "--memory", "8192"])

    # Used for filer - a fake machine for now
    def testaddfiler(self):
        self.noouttest(["add", "machine", "--machine", "filer1",
                        "--rack", "ut3", "--model", "hs21-8853l5u",
                        "--cpucount", "2", "--cpuvendor", "intel",
                        "--cpuname", "xeon", "--cpuspeed", "2660",
                        "--memory", "8192"])

    # Used for VPLS network tests
    def testaddut3c5n5(self):
        self.noouttest(["add", "machine", "--machine", "ut3c5n5",
                        "--rack", "ut3", "--model", "hs21-8853l5u",
                        "--cpucount", "2", "--cpuvendor", "intel",
                        "--cpuname", "xeon", "--cpuspeed", "2660",
                        "--memory", "8192"])

    # Test normalization
    def testaddnp3c5n5(self):
        self.noouttest(["add", "machine", "--machine", "np3C5N5",
                        "--rack", "np3", "--model", "hs21-8853l5u",
                        "--cpucount", "2", "--cpuvendor", "intel",
                        "--cpuname", "xeon", "--cpuspeed", "2660",
                        "--memory", "8192"])

    def testverifynormalization(self):
        command = "show machine --machine NP3c5N5"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: np3c5n5", command)

        command = "show machine --machine np3c5n5"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: np3c5n5", command)

    # Used for testing notifications
    def testaddut3c5n6(self):
        self.noouttest(["add", "machine", "--machine", "ut3c5n6",
                        "--rack", "ut3", "--model", "hs21-8853l5u",
                        "--cpucount", "2", "--cpuvendor", "intel",
                        "--cpuname", "xeon", "--cpuspeed", "2660",
                        "--memory", "8192"])

    # Network environment testing
    def testaddut3c5n7(self):
        self.noouttest(["add", "machine", "--machine", "ut3c5n7",
                        "--rack", "ut3", "--model", "hs21-8853l5u",
                        "--cpucount", "2", "--cpuvendor", "intel",
                        "--cpuname", "xeon", "--cpuspeed", "2660",
                        "--memory", "8192"])

    # Network environment testing
    def testaddut3c5n8(self):
        self.noouttest(["add", "machine", "--machine", "ut3c5n8",
                        "--rack", "ut3", "--model", "hs21-8853l5u",
                        "--cpucount", "2", "--cpuvendor", "intel",
                        "--cpuname", "xeon", "--cpuspeed", "2660",
                        "--memory", "8192"])

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
        self.matchoutput(out, "Cpu: xeon_2660 x 2", command)
        self.matchoutput(out, "Memory: 8192 MB", command)
        self.matchoutput(out, "Serial: KPDZ406", command)

    def testverifycatut3c1n3(self):
        command = "cat --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"location" = "ut.ny.na";', command)
        self.matchoutput(out, '"rack/name" = "ut3";', command)
        self.matchoutput(out, '"rack/row" = "a";', command)
        self.matchoutput(out, '"rack/column" = "3";', command)
        self.matchoutput(out, '"rack/room" = "utroom1";', command)
        self.matchoutput(out, '"serialnumber" = "KPDZ406";', command)
        self.matchoutput(out,
                         'include { "hardware/machine/ibm/hs21-8853l5u" };',
                         command)
        self.searchoutput(out,
                          r'"ram" = list\(\s*'
                          r'create\("hardware/ram/generic",\s*'
                          r'"size", 8192\*MB\s*\)\s*\);',
                          command)
        self.searchoutput(out,
                          r'"cpu" = list\(\s*'
                          r'create\("hardware/cpu/intel/xeon_2660"\),\s*'
                          r'create\("hardware/cpu/intel/xeon_2660"\s*\)\s*\);',
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
        self.matchoutput(out, "Cpu: xeon_2660 x 2", command)
        self.matchoutput(out, "Memory: 8192 MB", command)
        self.matchoutput(out, "Serial: KPDZ407", command)

    def testverifycatut3c1n4(self):
        command = "cat --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"location" = "ut.ny.na";', command)
        self.matchoutput(out, '"serialnumber" = "KPDZ407";', command)
        self.matchoutput(out,
                         'include { "hardware/machine/ibm/hs21-8853l5u" };',
                         command)
        self.searchoutput(out,
                          r'"ram" = list\(\s*'
                          r'create\("hardware/ram/generic",\s*'
                          r'"size", 8192\*MB\s*\)\s*\);',
                          command)
        self.searchoutput(out,
                          r'"cpu" = list\(\s*'
                          r'create\("hardware/cpu/intel/xeon_2660"\),\s*'
                          r'create\("hardware/cpu/intel/xeon_2660"\s*\)\s*\);',
                          command)

    def testaddccissmachine(self):
        self.noouttest(["add", "machine", "--machine", "ut3c1n8",
                        "--rack", "ut3", "--model", "utccissmodel"])

    def testverifyccissmachine(self):
        command = "show machine --machine ut3c1n8"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Rackmount: ut3c1n8", command)
        self.matchoutput(out, "Rack: ut3", command)
        self.matchoutput(out, "Vendor: hp Model: utccissmodel", command)
        self.matchoutput(out, "Cpu: xeon_2500 x 2", command)
        self.matchoutput(out, "Memory: 49152 MB", command)
        self.matchoutput(out, "Disk: c0d0 466 GB cciss (local) [boot]", command)

    def testverifycatut3c1n8(self):
        command = "cat --machine ut3c1n8"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"location" = "ut.ny.na";', command)
        self.matchoutput(out,
                         'include { "hardware/machine/hp/utccissmodel" };',
                         command)
        self.matchoutput(out,
                         'escape("cciss/c0d0"), '
                         'create("hardware/harddisk/generic/cciss",',
                         command)
        self.matchoutput(out,
                         '"capacity", 466*GB',
                         command)

    def testaddut3c1n9(self):
        self.noouttest(["add", "machine", "--machine", "ut3c1n9",
                        "--rack", "ut3", "--model", "hs21-8853l5u"])

    def testrejectqualifiedname(self):
        command = ["add", "machine", "--machine", "qualified.ms.com",
                   "--rack", "ut3", "--model", "hs21-8853l5u"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Illegal hardware label format 'qualified.ms.com'.",
                         command)

    # Testing that add machine does not allow a tor_switch....
    def testrejectut3gd2r01(self):
        command = ["add", "machine", "--machine", "ut3gd1r02",
                   "--rack", "ut3", "--model", "uttorswitch"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "cannot add machines of type switch",
                         command)

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
            "--cpuvendor", "intel", "--cpuname", "xeon", "--cpuspeed", "2500",
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

    def testaddutnorack(self):
        # A machine that's not in a rack
        self.noouttest(["add", "machine", "--machine", "utnorack",
            "--desk", "utdesk1", "--model", "poweredge_6650"])

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
        # The virtual machine tests require quite a bit of memory...
        for i in range(101, 150):
            port = i - 100
            self.noouttest(["add", "machine", "--machine", "ut10s04p%d" % port,
                            "--rack", "ut10", "--model", "vb1205xm",
                            "--memory", 81920])

    def testadd10gigracks(self):
        for port in range(1, 13):
            self.noouttest(["add", "machine", "--machine", "ut11s01p%d" % port,
                            "--rack", "ut11", "--model", "vb1205xm"])
            self.noouttest(["add", "machine", "--machine", "ut12s02p%d" % port,
                            "--rack", "ut12", "--model", "vb1205xm"])

    def testaddharacks(self):
        # Machines for metacluster high availability testing
        for port in range(1, 25):
            for rack in ["ut13", "np13"]:
                self.noouttest(["add", "machine",
                                "--machine", "%ss03p%d" % (rack, port),
                                "--rack", rack, "--model", "vb1205xm"])

    def testaddf5test(self):
        command = ["add", "machine", "--machine", "f5test", "--vendor", "f5",
                   "--model", "f5_model", "--rack", "ut3"]
        self.noouttest(command)

    def testverifymachineall(self):
        command = ["show", "machine", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "ut3c5n10", command)
        self.matchoutput(out, "ut3c1n3", command)
        self.matchoutput(out, "ut3c1n4", command)
        self.matchoutput(out, "ut3s01p1a", command)
        self.matchoutput(out, "ut3s01p1b", command)
        self.matchoutput(out, "ut8s02p1", command)
        self.matchoutput(out, "ut9s03p1", command)
        self.matchoutput(out, "ut10s04p1", command)
        self.matchoutput(out, "ut11s01p1", command)
        self.matchoutput(out, "f5test", command)

    # FIXME: Missing a test for adding a macihne to a chassis where the
    # fqdn given for the chassis isn't *actually* a chassis.
    # FIXME: Missing a test for chassis without a slot.  (May not be possible
    # with the aq client.)
    # FIXME: Missing a test for a location that conflicts with chassis loc.
    # FIXME: Missing a test for a slot without a chassis.  (May not be possible
    # with the aq client.)
    # FIXME: Add a test where the machine trying to be created already exists.

    # Note: More regression tests are in the test_add_virtual_hardware module.


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddMachine)
    unittest.TextTestRunner(verbosity=2).run(suite)
