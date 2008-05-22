#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Basic module for running tests on broker commands."""

import os
import sys
import unittest
from subprocess import Popen, PIPE

from aquilon.config import Config

class TestBrokerCommand(unittest.TestCase):

    def setUp(self):
        self.config = Config()

    def tearDown(self):
        pass

    def runcommand(self, command):
        aq = os.path.join(self.config.get("broker", "srcdir"), "bin", "aq")
        kncport = self.config.get("broker", "kncport")
        if isinstance(command, list):
            args = command[:]
        else:
            args = [command]
        args.insert(0, aq)
        args.insert(1, "--aqport")
        args.insert(2, kncport)
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        return p

    def commandtest(self, command):
        p = self.runcommand(command)
        (out, err) = p.communicate()
        self.assertEqual(err, "",
                "STDERR for %s was not empty:\n@@@\n'%s'\n@@@\n"
                % (command, err))
        self.assertEqual(p.returncode, 0,
                "Non-zero return code for %s, STDOUT:\n@@@\n'%s'\n@@@\n"
                % (command, out))
        return out

    def noouttest(self, command):
        out = self.commandtest(command)
        self.assertEqual(out, "",
                "STDOUT for %s was not empty:\n@@@\n'%s'\n@@@\n"
                % (command, out))

    # Right now, commands are not implemented consistently.  When that is
    # addressed, this unit test should be updated.
    def notfoundtest(self, command):
        p = self.runcommand(command)
        (out, err) = p.communicate()
        self.assertEqual(err, "",
                "STDERR for %s was not empty:\n@@@\n'%s'\n@@@\n"
                % (command, err))
        if p.returncode == 0:
            self.assertEqual(out, "",
                    "STDOUT for %s was not empty:\n@@@\n'%s'\n@@@\n"
                    % (command, out))
        else:
            self.assertEqual(p.returncode, 4)
            self.assertEqual(out.find("Not Found"), 0,
                    "STDOUT for %s did not start with Not Found:\n@@@\n'%s'\n@@@\n"
                    % (command, out))
        return

    def badrequesttest(self, command):
        p = self.runcommand(command)
        (out, err) = p.communicate()
        self.assertEqual(err, "",
                "STDERR for %s was not empty:\n@@@\n'%s'\n@@@\n"
                % (command, err))
        self.assertEqual(p.returncode, 4)
        self.assertEqual(out.find("Bad Request"), 0,
                "STDOUT for %s did not start with Bad Request:\n@@@\n'%s'\n@@@\n"
                % (command, out))
        return

    def matchoutput(self, out, s, command):
        self.assert_(out.find(s) >= 0, 
                "STDOUT for %s did not include '%s':\n@@@\n'%s'\n@@@\n"
                % (command, s, out))

    def matchclean(self, out, s, command):
        self.assert_(out.find(s) < 0, 
                "STDOUT for %s includes '%s':\n@@@\n'%s'\n@@@\n"
                % (command, s, out))


#if __name__=='__main__':

