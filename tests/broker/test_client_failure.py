#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing client error handling."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestClientFailure(TestBrokerCommand):

    def testinvalidaqhost(self):
        command = "status --aqhost=invalidhost"
        (p, out, err) = self.runcommand(command.split(" "))
        self.assertEqual(err,
                "Failed to connect to invalidhost: Unknown host.\n")
        self.assertEqual(out, "",
                "STDOUT for %s was not empty:\n@@@\n'%s'\n@@@\n"
                % (command, out))
        self.assertEqual(p.returncode, 1)

    def testnotrunningaqhost(self):
        command = "status --aqhost=%s" % self.host_not_running_aqd
        (p, out, err) = self.runcommand(command.split(" "))
        self.assertEqual(err,
                "Failed to connect to %s port %s: Connection refused.\n"
                % (self.host_not_running_aqd, 
                    self.config.get("broker", "kncport")))
        self.assertEqual(out, "",
                "STDOUT for %s was not empty:\n@@@\n'%s'\n@@@\n"
                % (command, out))
        self.assertEqual(p.returncode, 1)

    def testconflictingoptions(self):
        command = "add interface --mac 02:02:02:02:02:02 --interface eth0 " \
                  "--machine does-not-exist --ip 2.2.2.2"
        (p, out, err) = self.runcommand(command.split(" "))
        s = "error: Option or option group machine conflicts with ip"
        self.assert_(err.find(s) >= 0,
                "STDERR for %s did not include '%s':\n@@@\n'%s'\n@@@\n"
                % (command, s, err))
        self.assertEqual(out, "",
                "STDOUT for %s was not empty:\n@@@\n'%s'\n@@@\n"
                % (command, out))
        self.assertEqual(p.returncode, 2)

    def testhelp(self):
        command = "help"
        out = self.commandtest(command)
        self.matchoutput(out, "Available commands are:", command)

    def testunknowncommand(self):
        command = "command-does-not-exist"
        (p, out, err) = self.runcommand(command)
        self.matchoutput(err, "Available commands are:", command)
        self.matchoutput(err, "Command command-does-not-exist is not known!",
                         command)
        self.assertEqual(p.returncode, 2,
                "Return code for %s was %d instead of %d, STDOUT:\n@@@\n'%s'\n"
                % (command, p.returncode, 2, out))

    def testunauthorized(self):
        command = "flush"
        out = self.unauthorizedtest(command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestClientFailure)
    unittest.TextTestRunner(verbosity=2).run(suite)

