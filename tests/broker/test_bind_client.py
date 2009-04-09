#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2009 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the bind client command."""

import os
import sys
import re
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestBindClient(TestBrokerCommand):
    """Testing manually binding client to services.

    Once a client has been bound, you can't use it to test
    the auto-selection logic in make_aquilon.  Those tests
    are done exclusively with the chooser* services, which
    should not be used here.

    """

    def testbindafs(self):
        command = ["bind", "client", "--hostname", "unittest02.one-nyp.ms.com",
                   "--service", "afs", "--instance", "q.ny.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "unittest02.one-nyp.ms.com adding binding for "
                         "service afs instance q.ny.ms.com",
                         command)

    def testverifybindafs(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/afs/q.ny.ms.com", command)

    def testbinddns(self):
        command = ["bind", "client", "--hostname", "unittest02.one-nyp.ms.com",
                   "--service", "dns", "--instance", "nyinfratest"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "unittest02.one-nyp.ms.com adding binding for "
                         "service dns instance nyinfratest",
                         command)

    def testbindutsi1(self):
        command = ["bind", "client", "--hostname", "unittest00.one-nyp.ms.com",
                   "--service", "utsvc", "--instance", "utsi1"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "unittest00.one-nyp.ms.com adding binding for "
                         "service utsvc instance utsi1",
                         command)

    def testverifybindutsi1(self):
        command = "show host --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/utsvc/utsi1", command)

    def testbindutsi2(self):
        command = ["bind", "client", "--debug",
                   "--hostname", "unittest02.one-nyp.ms.com",
                   "--service", "utsvc", "--instance", "utsi2"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "Creating service Chooser", command)

    def testverifybindutsi2(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/utsvc/utsi2", command)

    def testverifybinddns(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/dns/nyinfratest", command)

    def testbindbootserver(self):
        command = ["bind", "client", "--hostname", "unittest02.one-nyp.ms.com",
                   "--service", "bootserver", "--instance", "np.test"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "unittest02.one-nyp.ms.com adding binding for "
                         "service bootserver instance np.test",
                         command)

    def testverifybindbootserver(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/bootserver/np.test", command)

    def testbindntp(self):
        command = ["bind", "client", "--hostname", "unittest02.one-nyp.ms.com",
                   "--service", "ntp", "--instance", "pa.ny.na"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "unittest02.one-nyp.ms.com adding binding for "
                         "service ntp instance pa.ny.na",
                         command)

    def testverifybindntp(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/ntp/pa.ny.na", command)

    # For unittest00, will test that afs and dns are bound by make aquilon
    # because they are required services.  Checking the service map
    # functionality for bind client, below.

    def testbindautobootserver(self):
        command = ["bind", "client", "--hostname", "unittest00.one-nyp.ms.com",
                   "--service", "bootserver"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "unittest00.one-nyp.ms.com adding binding for "
                         "service bootserver instance np.test",
                         command)

    def testverifybindautobootserver(self):
        command = "show host --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/bootserver/np.test", command)

    def testbindautontp(self):
        command = ["bind", "client", "--hostname", "unittest00.one-nyp.ms.com",
                   "--service", "ntp"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "unittest00.one-nyp.ms.com adding binding for "
                         "service ntp instance pa.ny.na",
                         command)

    def testverifybindautontp(self):
        command = "show host --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/ntp/pa.ny.na", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBindClient)
    unittest.TextTestRunner(verbosity=2).run(suite)

