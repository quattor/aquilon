#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2009 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing constraints in commands involving domain."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestServiceConstraints(TestBrokerCommand):

    def testdelrequiredservicepersonalitymissing(self):
        command = ["del_required_service", "--service=ntp",
                   "--archetype=windows", "--personality=desktop"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Could not find required service", command)

    def testdelservicewithinstances(self):
        command = "del service --service aqd"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out,
                         "Cannot remove service with instances defined",
                         command)

    def testverifydelservicewithinstances(self):
        command = "show service --service aqd"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: aqd", command)

    def testdelserviceinstancewithservers(self):
        command = "del service --service aqd --instance ny-prod"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out,
                         "instance is still being provided by servers",
                         command)

    def testverifydelserviceinstancewithservers(self):
        command = "show service --service aqd --instance ny-prod"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: aqd Instance: ny-prod", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestServiceConstraints)
    unittest.TextTestRunner(verbosity=2).run(suite)

