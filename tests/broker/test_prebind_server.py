#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" This is needed to make sure that a server is bound to the aqd service
    before make aquilon runs."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestPrebindServer(TestBrokerCommand):

    def testbindaqdserver(self):
        self.noouttest(["bind", "server",
            "--hostname", "nyaqd1.ms.com",
            "--service", "aqd", "--instance", "ny-prod"])

    def testverifybindutsi1(self):
        command = "show service --service aqd --instance ny-prod"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Server: nyaqd1.ms.com", command)

    def testbindchooser(self):
        for service in ["chooser1", "chooser2", "chooser3"]:
            for (s, n) in [(1, 'a'), (2, 'b'), (3, 'c')]:
                if service == 'chooser2' and n == 'b':
                    continue
                if service == 'chooser3' and n == 'c':
                    continue
                server = "server%d.aqd-unittest.ms.com" % s
                instance = "ut.%s" % n
                self.noouttest(["bind", "server", "--hostname", server,
                                "--service", service, "--instance", instance])


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBindServer)
    unittest.TextTestRunner(verbosity=2).run(suite)

