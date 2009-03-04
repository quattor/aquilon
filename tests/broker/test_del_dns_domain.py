#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the del dns_domain command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestDelDnsDomain(TestBrokerCommand):

    def testdelaqdunittestdomain(self):
        command = "del dns_domain --dns_domain aqd-unittest.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelaqdunittestdomain(self):
        command = "show dns_domain --dns_domain aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testverifydelaqdunittestdomainproto(self):
        command = ["show", "dns_domain", "--dns_domain=aqd-unittest.ms.com",
                   "--format=proto"]
        self.notfoundtest(command)

    def testverifyshowall(self):
        command = "show dns_domain --all"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "DNS Domain: aqd-unittest.ms.com", command)

    def testverifyshowallproto(self):
        command = "show dns_domain --all --format=proto"
        out = self.commandtest(command.split(" "))
        dns_domains = self.parse_dns_domainlist_msg(out).dns_domains
        dns_names = [d.name for d in dns_domains]
        for domain in ['aqd-unittest.ms.com']:
            self.failIf(domain in dns_names,
                        "Domain %s appears in list %s" % (domain, dns_names))


if __name__=='__main__':
    import aquilon.aqdb.depends
    import nose

    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelDnsDomain)
    #unittest.TextTestRunner(verbosity=2).run(suite)
    nose.runmodule()

