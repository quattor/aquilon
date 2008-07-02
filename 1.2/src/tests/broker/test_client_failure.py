#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
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
        p = self.runcommand(command.split(" "))
        (out, err) = p.communicate()
        self.assertEqual(err,
                "Failed to connect to invalidhost: Unknown host.\n")
        self.assertEqual(out, "",
                "STDOUT for %s was not empty:\n@@@\n'%s'\n@@@\n"
                % (command, out))
        self.assertEqual(p.returncode, 1)

    def testnotrunningaqhost(self):
        command = "status --aqhost=myweb"
        p = self.runcommand(command.split(" "))
        (out, err) = p.communicate()
        self.assertEqual(err,
                "Failed to connect to myweb port %s: Connection refused.\n"
                % self.config.get("broker", "kncport"))
        self.assertEqual(out, "",
                "STDOUT for %s was not empty:\n@@@\n'%s'\n@@@\n"
                % (command, out))
        self.assertEqual(p.returncode, 1)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestClientFailure)
    unittest.TextTestRunner(verbosity=2).run(suite)

