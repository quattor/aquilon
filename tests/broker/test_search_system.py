#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the search system command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestSearchSystem(TestBrokerCommand):

    def testfqdnavailable(self):
        command = "search system --fqdn unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))

    def testfqdnunavailablerealdomain(self):
        command = "search system --fqdn does-not-exist.one-nyp.ms.com"
        self.noouttest(command.split(" "))

    def testfqdnunavailablefakedomain(self):
        command = "search system --fqdn unittest00.does-not-exist.ms.com"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "DNS domain 'does-not-exist.ms.com'", command)

    def testfqdnavailablefull(self):
        command = "search system --fqdn unittest00.one-nyp.ms.com --fullinfo"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hostname: unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "Blade: ut3c1n3", command)

    def testdnsdomainavailable(self):
        command = "search system --dnsdomain aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "np997gd1r04.aqd-unittest.ms.com", command)
        self.matchoutput(out, "np998gd1r01.aqd-unittest.ms.com", command)
        self.matchoutput(out, "np999gd1r01.aqd-unittest.ms.com", command)
        self.matchoutput(out, "ut3gd1r01.aqd-unittest.ms.com", command)
        self.matchoutput(out, "ut3c1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "ut3c5.aqd-unittest.ms.com", command)

    def testdnsdomainunavailable(self):
        command = "search system --dnsdomain does-not-exist.ms.com"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "DnsDomain does-not-exist.ms.com not found",
                         command)

    def testshortnameavailable(self):
        command = "search system --shortname unittest00"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)

    def testshortnameunavailable(self):
        command = "search system --shortname does-not-exist"
        self.noouttest(command.split(" "))

    def testipavailable(self):
        command = "search system --ip %s" % self.hostip2
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)

    def testipunavailable(self):
        command = "search system --ip 4.2.2.4"
        self.noouttest(command.split(" "))

    def testnetworkipavailable(self):
        command = "search system --networkip 8.8.4.0"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "np997gd1r04.aqd-unittest.ms.com", command)
        self.matchoutput(out, "np999gd1r01.aqd-unittest.ms.com", command)
        self.matchoutput(out, "ut3c5.aqd-unittest.ms.com", command)
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest00-e1.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest00r.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest01.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest02.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest02rsa.one-nyp.ms.com", command)

    def testnetworkipunavailable(self):
        command = "search system --ip 4.2.2.0"
        self.noouttest(command.split(" "))

    def testmacavailable(self):
        command = "search system --mac %s" % self.hostmac2
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)

    def testmacunavailable(self):
        command = "search system --mac 02:02:02:02:02:02"
        self.noouttest(command.split(" "))

    def testall(self):
        command = "search system --all"
        out = self.commandtest(command.split(" "))
        # This is a good sampling, but not the full output
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest00r.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest00-e1.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest01.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest02.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest02rsa.one-nyp.ms.com", command)
        self.matchoutput(out, self.aurora_with_node, command)
        self.matchoutput(out, self.aurora_without_node, command)
        self.matchoutput(out, "ut3gd1r01.aqd-unittest.ms.com", command)
        self.matchoutput(out, "ut3c1.aqd-unittest.ms.com", command)

    def testallfull(self):
        command = "search system --all --fullinfo"
        out = self.commandtest(command.split(" "))
        # This is a good sampling, but not the full output
        self.matchoutput(out, "Hostname: unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest00r.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest00-e1.one-nyp.ms.com", command)
        self.matchoutput(out, "Hostname: unittest01.one-nyp.ms.com", command)
        self.matchoutput(out, "Hostname: unittest02.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest02rsa.one-nyp.ms.com", command)
        self.matchoutput(out, "Hostname: %s" % self.aurora_with_node, command)
        self.matchoutput(out, "Hostname: %s" % self.aurora_without_node,
                         command)
        self.matchoutput(out, "Tor_switch: ut3gd1r01.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Chassis: ut3c1.aqd-unittest.ms.com", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSearchSystem)
    unittest.TextTestRunner(verbosity=2).run(suite)

