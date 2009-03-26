#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the add required service command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestAddRequiredService(TestBrokerCommand):

    def testaddrequiredafs(self):
        command = "add required service --service afs --archetype aquilon"
        self.noouttest(command.split(" "))

    def testaddrequireddns(self):
        command = "add required service --service dns --archetype aquilon"
        self.noouttest(command.split(" "))

    def testaddrequiredaqd(self):
        command = "add required service --service aqd --archetype aquilon"
        self.noouttest(command.split(" "))

    def testaddrequiredntp(self):
        command = "add required service --service ntp --archetype aquilon"
        self.noouttest(command.split(" "))

    def testaddrequiredbootserver(self):
        command = ["add_required_service",
                   "--service=bootserver", "--archetype=aquilon"]
        self.noouttest(command)

    def testverifyaddrequiredservices(self):
        command = "show archetype --archetype aquilon"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: afs", command)
        self.matchoutput(out, "Service: aqd", command)
        self.matchoutput(out, "Service: bootserver", command)
        self.matchoutput(out, "Service: dns", command)
        self.matchoutput(out, "Service: ntp", command)

    def testaddrequiredpersonality(self):
        for service in ["chooser1", "chooser2", "chooser3"]:
            command = ["add_required_service", "--service", service,
                       "--archetype=aquilon", "--personality=unixeng-test"]
            self.noouttest(command)

    def testverifyaddrequiredpersonality(self):
        command = ["show_personality", "--archetype=aquilon",
                   "--name=unixeng-test"]
        out = self.commandtest(command)
        self.matchoutput(out, "Service: chooser1", command)
        self.matchoutput(out, "Service: chooser2", command)
        self.matchoutput(out, "Service: chooser3", command)

    def testaddrequiredutsvc(self):
        command = ["add_required_service", "--personality=compileserver",
                   "--service=utsvc", "--archetype=aquilon"]
        self.noouttest(command)

    def testverifyaddrequiredutsvc(self):
        command = ["show_personality", "--archetype=aquilon",
                   "--name=compileserver"]
        out = self.commandtest(command)
        self.matchoutput(out, "Service: utsvc", command)

    def testaddrequiredbadservice(self):
        command = ["add_required_service", "--service=badservice",
                   "--personality=badpersonality2", "--archetype=aquilon"]
        self.noouttest(command)

    def testverifyaddrequiredbadservice(self):
        command = ["show_personality", "--archetype=aquilon",
                   "--name=badpersonality2"]
        out = self.commandtest(command)
        self.matchoutput(out, "Service: badservice", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddRequiredService)
    unittest.TextTestRunner(verbosity=2).run(suite)

