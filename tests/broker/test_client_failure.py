#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Module for testing client error handling."""

import socket
import re

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
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
        # Reserve a port, but do not listen on it
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

        hostname = self.config.get("unittest", "hostname")
        short, domain = hostname.split('.', 1)

        command = ["status", "--aqport", port]
        (p, out, err) = self.runcommand(command)
        # This might be either 'Connection refused.' or 'Connection timed out.'.
        # There may also be variations in the output, like using the short or
        # full hostname.
        pattern = "Failed to connect to %s(\.%s)? port %d: " % (short, domain, port)
        self.assertTrue(re.match(pattern, err),
                        "Expected '%s' to start with '%s'" % (err, pattern))
        self.assertEqual(out, "",
                         "STDOUT for %s was not empty:\n@@@\n'%s'\n@@@\n"
                         % (command, out))
        self.assertEqual(p.returncode, 1)

    def testconflictingoptions(self):
        command = "add interface --mac 02:02:02:02:02:02 --interface eth0 " \
                  "--machine does-not-exist --switch does-not-exist-either"
        (p, out, err) = self.runcommand(command.split(" "))
        s = "error: Option or option group switch conflicts with machine"
        self.assert_(err.find(s) >= 0,
                     "STDERR for %s did not include '%s':\n@@@\n'%s'\n@@@\n"
                     % (command, s, err))
        self.assertEqual(out, "",
                         "STDOUT for %s was not empty:\n@@@\n'%s'\n@@@\n"
                         % (command, out))
        self.assertEqual(p.returncode, 2)

    def testextraargs(self):
        command = "show cpu --speed 2000 foo"
        (p, out, err) = self.runcommand(command.split(" "))
        s = "Extra arguments on the command line"
        self.assert_(err.find(s) >= 0,
                     "STDERR for %s did not include '%s':\n@@@\n'%s'\n@@@\n"
                     % (command, s, err))

    def testinvalidinteger(self):
        command = "show cpu --speed foo"
        (p, out, err) = self.runcommand(command.split(" "))
        s = "option --speed: invalid integer value: 'foo'"
        self.assert_(err.find(s) >= 0,
                     "STDERR for %s did not include '%s':\n@@@\n'%s'\n@@@\n"
                     % (command, s, err))

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
                         "Return code for %s was %d instead of %d, "
                         "STDOUT:\n@@@\n'%s'\n"
                         % (command, p.returncode, 2, out))

    def testunauthorized(self):
        command = "flush"
        out = self.unauthorizedtest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestClientFailure)
    unittest.TextTestRunner(verbosity=2).run(suite)
