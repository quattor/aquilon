#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the unbind client command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestUnbindClient(TestBrokerCommand):

    def testunbinduts(self):
        self.noouttest(["unbind", "client",
            "--hostname", "unittest02.one-nyp.ms.com",
            "--service", "utsvc"])

    def testverifyunbinduts(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Template: service/utsvc/utsi1", command)

    def testrejectunbindrequired(self):
        command = "unbind client --hostname unittest02.one-nyp.ms.com --service afs"
        self.badrequesttest(command.split(" "))

    def testzulu(self):
        # We want to put things back to how they were, in order
        # to allow later tests to see utsi1 with clients.
        # We can't use the fixtures, because the tests are stateful,
        # so we just specify this as another test to run last.
        self.noouttest(["bind", "client",
            "--hostname", "unittest02.one-nyp.ms.com",
            "--service", "utsvc", "--instance", "utsi2"])

if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUnbindClient)
    unittest.TextTestRunner(verbosity=2).run(suite)

