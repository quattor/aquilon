#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2009 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the add os command."""


import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestAddOS(TestBrokerCommand):

    def testaddexisting(self):
        command = "add os --archetype aquilon --os linux --vers 4.0.1-x86_64"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "OS version 'linux/4.0.1-x86_64' already exists",
                         command)

    def testaddbadname(self):
        command = "add os --archetype aquilon --os oops@! --vers 1.0"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "OS name 'oops@!' is not valid", command)

    def testaddbadversion(self):
        command = "add os --archetype aquilon --os newos --vers oops@!"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "OS version 'oops@!' is not valid", command)

    def testaddutos(self):
        command = "add os --archetype utarchetype1 --os utos --vers 1.0"
        self.noouttest(command.split(" "))

    def testverifyutos(self):
        command = "show os --archetype utarchetype1 --os utos --vers 1.0"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: os/utos/1.0", command)
        self.matchclean(out, "linux", command)

    def testverifyosonly(self):
        command = "show os --os utos"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: os/utos/1.0", command)
        self.matchclean(out, "linux", command)

    def testverifyversonly(self):
        command = "show os --vers 1.0"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: os/utos/1.0", command)
        self.matchclean(out, "linux", command)

    def testverifyall(self):
        command = "show os --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: os/utos/1.0", command)
        self.matchoutput(out, "Template: os/linux/4.0.1-x86_64", command)

    def testshownotfound(self):
        command = "show os --os os-does-not-exist"
        self.notfoundtest(command.split(" "))


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddOS)
    unittest.TextTestRunner(verbosity=2).run(suite)

