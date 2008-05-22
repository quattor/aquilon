#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the bind client command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestBindClient(TestBrokerCommand):

    def testbindafs(self):
        self.noouttest(["bind", "client",
            "--hostname", "aquilon02.one-nyp.ms.com",
            "--service", "afs", "--instance", "q.ny.ms.com"])

    def testverifybindafs(self):
        command = "show host --hostname aquilon02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/afs/q.ny.ms.com", command)

    def testbinddns(self):
        self.noouttest(["bind", "client",
            "--hostname", "aquilon02.one-nyp.ms.com",
            "--service", "dns", "--instance", "nyinfratest"])

    def testverifybinddns(self):
        command = "show host --hostname aquilon02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/dns/nyinfratest", command)

    def testbindbootserver(self):
        self.noouttest(["bind", "client",
            "--hostname", "aquilon02.one-nyp.ms.com",
            "--service", "bootserver", "--instance", "np.test"])

    def testverifybindbootserver(self):
        command = "show host --hostname aquilon02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/bootserver/np.test", command)

    def testbindntp(self):
        self.noouttest(["bind", "client",
            "--hostname", "aquilon02.one-nyp.ms.com",
            "--service", "ntp", "--instance", "pa.ny.na"])

    def testverifybindntp(self):
        command = "show host --hostname aquilon02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/ntp/pa.ny.na", command)

    # For aquilon00, will test that afs and dns are bound by make aquilon
    # because they are required services.  Checking the service map
    # functionality for bind client, below.

    def testbindautobootserver(self):
        self.noouttest(["bind", "client",
            "--hostname", "aquilon00.one-nyp.ms.com",
            "--service", "bootserver"])

    def testverifybindautobootserver(self):
        command = "show host --hostname aquilon00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/bootserver/np.test", command)

    def testbindautontp(self):
        self.noouttest(["bind", "client",
            "--hostname", "aquilon00.one-nyp.ms.com",
            "--service", "ntp"])

    def testverifybindautontp(self):
        command = "show host --hostname aquilon00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/ntp/pa.ny.na", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBindClient)
    unittest.TextTestRunner(verbosity=2).run(suite)

