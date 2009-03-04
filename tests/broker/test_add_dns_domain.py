#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the add dns domain command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestAddDnsDomain(TestBrokerCommand):

    def testaddaqdunittestdomain(self):
        self.noouttest(["add", "dns_domain",
            "--dns_domain", "aqd-unittest.ms.com"])

    def testverifyaddaqdunittestdomain(self):
        command = "show dns_domain --dns_domain aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "DNS Domain: aqd-unittest.ms.com", command)

    def testverifyaddaqdunittestdomaincsv(self):
        command = "show dns_domain --dns_domain aqd-unittest.ms.com --format=csv"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "aqd-unittest.ms.com,", command)

    def testverifyaddaqdunittestdomainproto(self):
        command = ["show", "dns_domain", "--dns_domain=aqd-unittest.ms.com",
                   "--format=proto"]
        out = self.commandtest(command)
        domain = self.parse_dns_domainlist_msg(out, expect=1).dns_domains[0]
        self.failUnlessEqual(domain.name, 'aqd-unittest.ms.com')

    def testverifyshowall(self):
        command = "show dns_domain --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "DNS Domain: aqd-unittest.ms.com", command)

    def testverifyshowallproto(self):
        command = "show dns_domain --all --format=proto"
        out = self.commandtest(command.split(" "))
        dns_domains = self.parse_dns_domainlist_msg(out).dns_domains
        dns_names = [d.name for d in dns_domains]
        for domain in ['ms.com', 'aqd-unittest.ms.com']:
            self.failUnless(domain in dns_names,
                            "Domain %s not in list %s" % (domain, dns_names))


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddDnsDomain)
    unittest.TextTestRunner(verbosity=2).run(suite)

