#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the add aurora host command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestAddAuroraHost(TestBrokerCommand):

    def testaddaurorawithnode(self):
        self.noouttest(["add", "aurora", "host",
            "--hostname", self.aurora_with_node])

    def testverifyaddaurorawithnode(self):
        command = "show host --hostname %s.ms.com" % self.aurora_with_node
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hostname: %s" % self.aurora_with_node, command)
        self.matchoutput(out, "Aurora_node: ", command)
        self.matchoutput(out, "Chassis: ", command)
        self.matchoutput(out, "Archetype: aurora", command)
        self.matchoutput(out, "Domain: aurora_domain", command)
        self.matchoutput(out, "Status: production", command)

    def testaddaurorawithoutnode(self):
        self.noouttest(["add", "aurora", "host",
            "--hostname", self.aurora_without_node])

    def testverifyaddaurorawithoutnode(self):
        command = "show host --hostname %s.ms.com" % self.aurora_without_node
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hostname: %s" % self.aurora_without_node,
                command)
        self.matchoutput(out, "Aurora_node: ", command)
        self.matchoutput(out, "Building: ", command)
        self.matchoutput(out, "Archetype: aurora", command)
        self.matchoutput(out, "Domain: aurora_domain", command)
        self.matchoutput(out, "Status: production", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddAuroraHost)
    unittest.TextTestRunner(verbosity=2).run(suite)

