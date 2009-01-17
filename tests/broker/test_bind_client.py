#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
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
import re
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand

# Testing manually binding client to services.
# Once a client has been bound, you can't use it to test
# the auto-selection logic in make_aquilon, so check
# any changes against that test (which happens after this
# one).

# The test assumes that hosts unittest00 and unittest02
# are defined and that the services afs, dns, uts are defined.
# At the end of this test, we will leave the state such that:
#
#  unittest00:
#     afs        = None (for later testing in make_aquilon)
#     bootserver = np.test (via map)
#     dns        = None (for later testing in make_aquilon)
#     ntp        = pa.ny.na (via map)
#     utsvc      = utsi1
#
#  unittest02:
#     afs        = q.ny.ms.com
#     bootserver = np.test
#     dns        = nyinfratest
#     ntp        = pa.ny.na
#     utsvc      = utsi2

class TestBindClient(TestBrokerCommand):

    def testbindafs(self):
        self.noouttest(["bind", "client",
            "--hostname", "unittest02.one-nyp.ms.com",
            "--service", "afs", "--instance", "q.ny.ms.com"])

    def testverifybindafs(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/afs/q.ny.ms.com", command)

    def testbinddns(self):
        self.noouttest(["bind", "client",
            "--hostname", "unittest02.one-nyp.ms.com",
            "--service", "dns", "--instance", "nyinfratest"])

    def testbindutsauto(self):
        # Bind two clients using the service map, then
        # check that the instances were correctly balanced
        self.noouttest(["bind", "client",
            "--hostname", "unittest00.one-nyp.ms.com",
            "--service", "utsvc"])
        self.noouttest(["bind", "client",
            "--hostname", "unittest02.one-nyp.ms.com",
            "--service", "utsvc"])
        command = "show service --service utsvc"
        out = self.commandtest(command.split(" "))
        count_re = re.compile(r'Client Count: (\d+)')
        inst_count = 0
        for m in count_re.finditer(out):
            inst_count += 1
            self.assert_(int(m.group(1)) > 0,
                    "Service Instance of utsvc has a client count <= 0:\n@@@\n'%s'\n@@@\n" %
                    out)
        self.assert_(inst_count > 1,
                "Not enough utsvc service instances found:\n@@@\n'%s'\n@@@\n" % out)
        # put the state back to normal to allow further testing
        command = "unbind client --host unittest00.one-nyp.ms.com --service utsvc"
        self.noouttest(command.split(" "))
        command = "unbind client --host unittest02.one-nyp.ms.com --service utsvc"
        self.noouttest(command.split(" "))

    def testbindutsi1(self):
        self.noouttest(["bind", "client",
            "--hostname", "unittest00.one-nyp.ms.com",
            "--service", "utsvc", "--instance", "utsi1"])

    def testverifybindutsi1(self):
        command = "show host --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/utsvc/utsi1", command)

    def testbindutsi2(self):
        self.noouttest(["bind", "client",
            "--hostname", "unittest02.one-nyp.ms.com",
            "--service", "utsvc", "--instance", "utsi2"])

    def testverifybindutsi2(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/utsvc/utsi2", command)

    def testverifybinddns(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/dns/nyinfratest", command)

    def testbindbootserver(self):
        self.noouttest(["bind", "client",
            "--hostname", "unittest02.one-nyp.ms.com",
            "--service", "bootserver", "--instance", "np.test"])

    def testverifybindbootserver(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/bootserver/np.test", command)

    def testbindntp(self):
        self.noouttest(["bind", "client",
            "--hostname", "unittest02.one-nyp.ms.com",
            "--service", "ntp", "--instance", "pa.ny.na"])

    def testverifybindntp(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/ntp/pa.ny.na", command)

    # For unittest00, will test that afs and dns are bound by make aquilon
    # because they are required services.  Checking the service map
    # functionality for bind client, below.

    def testbindautobootserver(self):
        self.noouttest(["bind", "client",
            "--hostname", "unittest00.one-nyp.ms.com",
            "--service", "bootserver"])

    def testverifybindautobootserver(self):
        command = "show host --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/bootserver/np.test", command)

    def testbindautontp(self):
        self.noouttest(["bind", "client",
            "--hostname", "unittest00.one-nyp.ms.com",
            "--service", "ntp"])

    def testverifybindautontp(self):
        command = "show host --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/ntp/pa.ny.na", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBindClient)
    unittest.TextTestRunner(verbosity=2).run(suite)

