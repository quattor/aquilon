#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the add tor_switch command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestAddTorSwitch(TestBrokerCommand):

    def testaddut3gd1r01(self):
        self.noouttest(["add", "tor_switch", "--tor_switch", "ut3gd1r01",
            "--rack", "ut3", "--model", "uttorswitch", "--serial", "SNgd1r01"])

    def verifyswitch(self, tor_switch, rack, rackrow, rackcol, serial=None):
        command = "show tor_switch --tor_switch %s" % tor_switch
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Tor_switch: %s" % tor_switch, command)
        self.matchoutput(out, "Rack: %s" % rack, command)
        self.matchoutput(out, "Row: %s" % rackrow, command)
        self.matchoutput(out, "Column: %s" % rackcol, command)
        self.matchoutput(out, "Vendor: hp Model: uttorswitch", command)
        self.matchoutput(out, "Cpu: Cpu xeon_2500 x 1", command)
        self.matchoutput(out, "Memory: 8192 MB", command)
        if serial:
            self.matchoutput(out, "Serial: %s" % serial, command)
        else:
            self.matchclean(out, "Serial:", command)
        for port in range(1,49):
            self.matchoutput(out, "Switch Port %d" % port, command)
        return (out, command)

    def testverifyaddut3gd1r01(self):
        self.verifyswitch("ut3gd1r01", "ut3", "a", "3", "SNgd1r01")

    def testverifyaddut3gd1r01csv(self):
        command = "show tor_switch --tor_switch ut3gd1r01 --format=csv"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ut3gd1r01,ut3,ut,hp,uttorswitch,SNgd1r01,,,",
                command)

    def testverifycatut3gd1r01(self):
        command = "cat --machine ut3gd1r01"
        self.badrequesttest(command.split(" "))

    # Testing that add machine does not allow a tor_switch....
    def testrejectut3gd1r02(self):
        self.badrequesttest(["add", "machine", "--machine", "ut3gd1r02",
            "--rack", "ut3", "--model", "uttorswitch"])

    def testverifyrejectut3gd1r02(self):
        command = "show machine --machine ut3gd1r02"
        out = self.notfoundtest(command.split(" "))

    # Testing that add tor_switch does not allow a blade....
    def testrejectut3gd1r03(self):
        self.badrequesttest(["add", "tor_switch", "--tor_switch", "ut3gd1r03",
            "--rack", "ut3", "--model", "hs21"])

    def testverifyrejectut3gd1r03(self):
        command = "show machine --machine ut3gd1r03"
        out = self.notfoundtest(command.split(" "))

    # Test adding a switch with an existing rack using --rackid
    def testaddnp997gd1r04(self):
        self.noouttest(["add", "tor_switch", "--tor_switch", "np997gd1r04",
            "--building", "np", "--rackid", "997",
            "--rackrow", "zz", "--rackcol", "99",
            "--model", "uttorswitch"])

    def testverifynp997gd1r04(self):
        self.verifyswitch("np997gd1r04", "np997", "zz", "99")

    def testverifyaddnp997gd1r04csv(self):
        command = "show tor_switch --tor_switch np997gd1r04 --format=csv"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "np997gd1r04,np997,np,hp,uttorswitch,,,", command)

    # Test adding a switch and creating a new rack
    def testaddnp998gd1r01(self):
        self.noouttest(["add", "tor_switch", "--tor_switch", "np998gd1r01",
            "--building", "np", "--rackid", "998",
            "--rackrow", "yy", "--rackcol", "88",
            "--model", "uttorswitch"])

    def testverifynp998gd1r01(self):
        self.verifyswitch("np998gd1r01", "np998", "yy", "88")

    def testverifyaddnp998gd1r01csv(self):
        command = "show tor_switch --tor_switch np998gd1r01 --format=csv"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "np998gd1r01,np998,np,hp,uttorswitch,,,", command)

    # Test adding a switch, creating a new rack, and adding an IP.
    def testaddnp999gd1r01(self):
        self.noouttest(["add", "tor_switch", "--tor_switch", "np999gd1r01",
            "--building", "np", "--rackid", "999",
            "--rackrow", "zz", "--rackcol", "11",
            "--model", "uttorswitch",
            "--interface", "xge49",
            "--mac", self.hostmac5, "--ip", self.hostip5])

    def testverifynp999gd1r01(self):
        (out, command) = self.verifyswitch("np999gd1r01", "np999", "zz", "11")
        self.matchoutput(out, "Interface: xge49 %s %s boot=False" %
                (self.hostmac5, self.hostip5), command)

    def testverifyaddnp999gd1r01csv(self):
        command = "show tor_switch --tor_switch np999gd1r01 --format=csv"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "np999gd1r01,np999,np,hp,uttorswitch,,xge49,%s,%s" %
                (self.hostmac5, self.hostip5), command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddTorSwitch)
    unittest.TextTestRunner(verbosity=2).run(suite)

