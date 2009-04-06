#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the add personality command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestAddPersonality(TestBrokerCommand):

    def testaddutpersonality(self):
        command = "add personality --name utpersonality --archetype aquilon"
        self.noouttest(command.split(" "))

    def testverifyaddutpersonality(self):
        command = "show personality --name utpersonality --archetype aquilon"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Personality: utpersonality Archetype: aquilon",
                         command)
        self.matchoutput(out, "Template: personality/utpersonality", command)
        self.matchclean(out, "Personality: inventory Archetype: aquilon",
                        command)
        self.matchclean(out, "Template: personality/inventory", command)

    def testverifyshowpersonalityall(self):
        command = "show personality --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Personality: utpersonality Archetype: aquilon",
                         command)
        self.matchoutput(out, "Template: personality/utpersonality", command)
        self.matchoutput(out, "Personality: generic Archetype: aurora",
                         command)
        self.matchoutput(out, "Template: personality/generic", command)

    def testverifyshowpersonalityarchetype(self):
        command = "show personality --archetype aquilon"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Personality: utpersonality Archetype: aquilon",
                         command)
        self.matchoutput(out, "Template: personality/utpersonality", command)
        self.matchoutput(out, "Personality: inventory Archetype: aquilon",
                         command)
        self.matchoutput(out, "Template: personality/inventory", command)
        self.matchclean(out, "Personality: generic Archetype: aurora",
                        command)
        self.matchclean(out, "Template: personality/generic", command)

    def testshowarchetypeunavailable(self):
        command = "show personality --archetype archetype-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Archetype archetype-does-not-exist", command)

    def testshowarchetypeunavailable2(self):
        command = ["show", "personality",
                   "--archetype", "archetype-does-not-exist",
                   "--name", "personality-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Archetype archetype-does-not-exist", command)

    def testshowpersonalityunavailable(self):
        command = ["show", "personality", "--archetype", "aquilon",
                   "--name", "personality-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Personality personality-does-not-exist",
                         command)

    def testshowpersonalityunavailable2(self):
        command = ["show", "personality",
                   "--name", "personality-does-not-exist"]
        self.noouttest(command)

    def testshowpersonalityname(self):
        command = "show personality --name generic"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Personality: generic Archetype: aurora",
                         command)
        self.matchoutput(out, "Template: personality/generic", command)
        self.matchoutput(out, "Personality: generic Archetype: windows",
                         command)
        self.matchoutput(out, "Template: personality/generic", command)

    def testaddwindowsdesktop(self):
        command = "add personality --name desktop --archetype windows"
        self.noouttest(command.split(" "))

    def testverifyaddwindowsdesktop(self):
        command = "show personality --name desktop --archetype windows"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Personality: desktop Archetype: windows",
                         command)
        self.matchoutput(out, "Template: personality/desktop", command)

    def testaddbadaquilonpersonality(self):
        # This personality is 'bad' because there will not be a set of
        # templates defined for it in the repository.
        command = "add personality --name badpersonality --archetype aquilon"
        self.noouttest(command.split(" "))

    def testverifybadaquilonpersonality(self):
        command = "show personality --name badpersonality --archetype aquilon"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Personality: badpersonality Archetype: aquilon",
                         command)
        self.matchoutput(out, "Template: personality/badpersonality", command)

    def testaddbadaquilonpersonality2(self):
        # This personality is double 'bad'... there will be a required
        # service for the personality that has no instances.
        command = "add personality --name badpersonality2 --archetype aquilon"
        self.noouttest(command.split(" "))

    def testverifybadaquilonpersonality2(self):
        command = "show personality --name badpersonality2 --archetype aquilon"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Personality: badpersonality2 Archetype: aquilon",
                         command)
        self.matchoutput(out, "Template: personality/badpersonality2", command)

    def testaddinvalidpersonalityname(self):
        command = ["add_personality", "--name", "this is a bad; name",
                   "--archetype", "aquilon"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "name 'this is a bad; name' is not valid",
                         command)

    def testaddduplicate(self):
        command = ["add_personality", "--name", "inventory",
                   "--archetype", "aquilon"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "already exists", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddPersonality)
    unittest.TextTestRunner(verbosity=2).run(suite)

