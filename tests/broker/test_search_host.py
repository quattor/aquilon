#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the search host command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestSearchHost(TestBrokerCommand):

    def testfqdnavailable(self):
        command = "search host --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)

    def testfqdnunavailablerealdomain(self):
        command = "search host --hostname does-not-exist.one-nyp.ms.com"
        self.noouttest(command.split(" "))

    def testfqdnunavailablefakedomain(self):
        command = "search host --hostname unittest00.does-not-exist.ms.com"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "DNS domain 'does-not-exist.ms.com'", command)

    def testfqdnavailablefull(self):
        command = "search host --hostname unittest00.one-nyp.ms.com --fullinfo"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hostname: unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "Blade: ut3c1n3", command)

    def testmachineavailable(self):
        command = "search host --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)

    def testmachineunavailable(self):
        command = "search host --machine machine-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Machine machine-does-not-exist not found",
                         command)

    def testdnsdomainavailable(self):
        command = "search host --dnsdomain aqd-unittest.ms.com"
        self.noouttest(command.split(" "))

    def testdnsdomainunavailable(self):
        command = "search host --dnsdomain does-not-exist.ms.com"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "DnsDomain does-not-exist.ms.com not found",
                         command)

    def testshortnameavailable(self):
        command = "search host --shortname unittest00"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)

    def testshortnameunavailable(self):
        command = "search host --shortname does-not-exist"
        self.noouttest(command.split(" "))

    def testdomainavailable(self):
        command = "search host --domain unittest"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest02.one-nyp.ms.com", command)

    def testdomainunavailable(self):
        command = "search host --domain domain-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Domain domain-does-not-exist not found",
                         command)

    def testarchetypeavailable(self):
        command = "search host --archetype aquilon"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest02.one-nyp.ms.com", command)

    def testarchetypeunavailable(self):
        command = "search host --archetype archetype-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Archetype archetype-does-not-exist not found",
                         command)

    def testbuildstatusavailable(self):
        command = "search host --buildstatus ready"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest02.one-nyp.ms.com", command)
        self.matchoutput(out, self.aurora_with_node, command)
        self.matchoutput(out, self.aurora_without_node, command)

    def testbuildstatusunavailable(self):
        command = "search host --buildstatus status-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Status status-does-not-exist not found",
                         command)

    def testipavailable(self):
        command = "search host --ip %s" % self.hostip2
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)

    def testipunavailable(self):
        command = "search host --ip 4.2.2.4"
        self.noouttest(command.split(" "))

    def testnetworkipavailable(self):
        command = "search host --networkip 8.8.4.0"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)
        self.matchclean(out, "unittest00-e1.one-nyp.ms.com", command)
        self.matchclean(out, "unittest00r.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest01.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest02.one-nyp.ms.com", command)
        self.matchclean(out, "unittest02rsa.one-nyp.ms.com", command)

    def testnetworkipunavailable(self):
        command = "search host --ip 4.2.2.0"
        self.noouttest(command.split(" "))

    def testmacavailable(self):
        command = "search host --mac %s" % self.hostmac2
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)

    def testmacunavailable(self):
        command = "search host --mac 02:02:02:02:02:02"
        self.noouttest(command.split(" "))

    def testall(self):
        command = "search host --all"
        out = self.commandtest(command.split(" "))
        # This is a good sampling, but not the full output
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)
        self.matchclean(out, "unittest00r.one-nyp.ms.com", command)
        self.matchclean(out, "unittest00-e1.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest01.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest02.one-nyp.ms.com", command)
        self.matchclean(out, "unittest02rsa.one-nyp.ms.com", command)
        self.matchoutput(out, self.aurora_with_node, command)
        self.matchoutput(out, self.aurora_without_node, command)
        self.matchclean(out, "ut3gd1r01.aqd-unittest.ms.com", command)
        self.matchclean(out, "ut3c1.aqd-unittest.ms.com", command)

    def testallfull(self):
        command = "search host --all --fullinfo"
        out = self.commandtest(command.split(" "))
        # This is a good sampling, but not the full output
        self.matchoutput(out, "Hostname: unittest00.one-nyp.ms.com", command)
        # Will work after a merge...
        #self.matchoutput(out, "unittest00r.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest00-e1.one-nyp.ms.com", command)
        self.matchoutput(out, "Hostname: unittest01.one-nyp.ms.com", command)
        self.matchoutput(out, "Hostname: unittest02.one-nyp.ms.com", command)
        # Will work after a merge...
        #self.matchoutput(out, "unittest02rsa.one-nyp.ms.com", command)
        self.matchoutput(out, "Hostname: %s" % self.aurora_with_node, command)
        self.matchoutput(out, "Hostname: %s" % self.aurora_without_node,
                         command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSearchHost)
    unittest.TextTestRunner(verbosity=2).run(suite)

