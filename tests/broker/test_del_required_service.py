#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2009 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the del required service command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestDelRequiredService(TestBrokerCommand):

    def testdelrequiredafs(self):
        command = "del required service --service afs --archetype aquilon"
        self.noouttest(command.split(" "))

    def testdelrequireddns(self):
        command = "del required service --service dns --archetype aquilon"
        self.noouttest(command.split(" "))

    def testdelrequiredaqd(self):
        command = "del required service --service aqd --archetype aquilon"
        self.noouttest(command.split(" "))

    def testdelrequiredntp(self):
        command = "del required service --service ntp --archetype aquilon"
        self.noouttest(command.split(" "))

    def testdelrequiredbootserver(self):
        command = ["del_required_service",
                   "--service=bootserver", "--archetype=aquilon"]
        self.noouttest(command)

    def testverifydelrequiredservices(self):
        command = "show archetype --archetype aquilon"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Service: afs", command)
        self.matchclean(out, "Service: aqd", command)
        self.matchclean(out, "Service: bootserver", command)
        self.matchclean(out, "Service: dns", command)
        self.matchclean(out, "Service: ntp", command)

    def testdelrequiredpersonality(self):
        for service in ["chooser1", "chooser2", "chooser3"]:
            command = ["del_required_service", "--service", service,
                       "--archetype=aquilon", "--personality=unixeng-test"]
            self.noouttest(command)

    def testverifydelrequiredpersonality(self):
        command = ["show_personality", "--archetype=aquilon",
                   "--personality=unixeng-test"]
        out = self.commandtest(command)
        self.matchclean(out, "Service: chooser1", command)
        self.matchclean(out, "Service: chooser2", command)
        self.matchclean(out, "Service: chooser3", command)

    def testdelrequiredbadpersonality(self):
        command = ["del_required_service", "--service", "badservice",
                   "--archetype=aquilon", "--personality=badpersonality2"]
        self.noouttest(command)

    def testverifydelrequiredbadpersonality(self):
        command = ["show_personality", "--archetype=aquilon",
                   "--personality=badpersonality2"]
        out = self.commandtest(command)
        self.matchclean(out, "Service: badservice", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelRequiredService)
    unittest.TextTestRunner(verbosity=2).run(suite)
