#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Module for testing client error handling."""

import unittest
import socket
import re

if __name__ == "__main__":
    import utils
    utils.import_depends()

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
                "Return code for %s was %d instead of %d, STDOUT:\n@@@\n'%s'\n"
                % (command, p.returncode, 2, out))

    def testunauthorized(self):
        command = "flush"
        out = self.unauthorizedtest(command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestClientFailure)
    unittest.TextTestRunner(verbosity=2).run(suite)

