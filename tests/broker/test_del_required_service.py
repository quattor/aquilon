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

    def testverifydelrequiredafs(self):
        command = "show archetype --archetype aquilon"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Service: afs", command)

    def testdelrequireddns(self):
        command = "del required service --service dns --archetype aquilon"
        self.noouttest(command.split(" "))

    def testverifydelrequireddns(self):
        command = "show archetype --archetype aquilon"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Service: dns", command)

    # This is lame.  Will be fixed in a few commits.
    def testdelrequiredpersonality(self):
        command = ["del_required_service", "--service=aqd",
                   "--archetype=aquilon", "--personality=compileserver"]
        self.noouttest(command)

    def testverifydelrequiredpersonality(self):
        command = ["show_personality", "--archetype=aquilon",
                   "--name=compileserver"]
        out = self.commandtest(command)
        self.matchclean(out, "Service: aqd", command)

if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelRequiredService)
    unittest.TextTestRunner(verbosity=2).run(suite)

