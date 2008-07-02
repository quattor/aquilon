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
        if self.config.has_option("unittest", "scratchdir"):
            self.scratchdir = self.config.get("unittest", "scratchdir")
            if not os.path.exists(self.scratchdir):
                os.path.makedirs(self.scratchdir)

    def tearDown(self):
        pass

    def runcommand(self, command, **kwargs):
        aq = os.path.join(self.config.get("broker", "srcdir"), "bin", "aq")
        kncport = self.config.get("broker", "kncport")
        if isinstance(command, list):
            args = command[:]
        else:
            args = [command]
        args.insert(0, aq)
        args.append("--aqport")
        args.append(kncport)
        if kwargs.has_key("env"):
            # Make sure that kerberos tickets are still present if the
            # environment is being overridden...
            env = {}
            for (key, value) in kwargs["env"].items():
                env[key] = value
            for (key, value) in os.environ.items():
                if key.find("KRB") == 0 and key not in env:
                    env[key] = value
            kwargs["env"] = env
        p = Popen(args, stdout=PIPE, stderr=PIPE, **kwargs)
        return p

    def commandtest(self, command, **kwargs):
        p = self.runcommand(command, **kwargs)
        (out, err) = p.communicate()
        self.assertEqual(err, "",
                "STDERR for %s was not empty:\n@@@\n'%s'\n@@@\n"
                % (command, err))
        self.assertEqual(p.returncode, 0,
                "Non-zero return code for %s, STDOUT:\n@@@\n'%s'\n@@@\n"
                % (command, out))
        return out

    def noouttest(self, command, **kwargs):
        out = self.commandtest(command, **kwargs)
        self.assertEqual(out, "",
                "STDOUT for %s was not empty:\n@@@\n'%s'\n@@@\n"
                % (command, out))

    def ignoreoutputtest(self, command, **kwargs):
        p = self.runcommand(command, **kwargs)
        (out, err) = p.communicate()
        # Ignore out/err unless we get a non-zero return code, then log it.
        self.assertEqual(p.returncode, 0,
                "Non-zero return code for %s, STDOUT:\n@@@\n'%s'\n@@@\nSTDERR:\n@@@\n'%s'\n@@@\n"
                % (command, out, err))
        return

    # Right now, commands are not implemented consistently.  When that is
    # addressed, this unit test should be updated.
    def notfoundtest(self, command, **kwargs):
        p = self.runcommand(command, **kwargs)
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

    def badrequesttest(self, command, **kwargs):
        p = self.runcommand(command, **kwargs)
        (out, err) = p.communicate()
        self.assertEqual(err, "",
                "STDERR for %s was not empty:\n@@@\n'%s'\n@@@\n"
                % (command, err))
        self.assertEqual(p.returncode, 4)
        self.assertEqual(out.find("Bad Request"), 0,
                "STDOUT for %s did not start with Bad Request:\n@@@\n'%s'\n@@@\n"
                % (command, out))
        return

    def internalerrortest(self, command, **kwargs):
        p = self.runcommand(command, **kwargs)
        (out, err) = p.communicate()
        self.assertEqual(err, "",
                "STDERR for %s was not empty:\n@@@\n'%s'\n@@@\n"
                % (command, err))
        self.assertEqual(p.returncode, 5)
        self.assertEqual(out.find("Internal Server Error"), 0,
                "STDOUT for %s did not start with Internal Server Error:\n@@@\n'%s'\n@@@\n"
                % (command, out))
        return out

    def matchoutput(self, out, s, command):
        self.assert_(out.find(s) >= 0, 
                "STDOUT for %s did not include '%s':\n@@@\n'%s'\n@@@\n"
                % (command, s, out))

    def matchclean(self, out, s, command):
        self.assert_(out.find(s) < 0, 
                "STDOUT for %s includes '%s':\n@@@\n'%s'\n@@@\n"
                % (command, s, out))

    def gitenv(self, env=None):
        git_path = self.config.get("broker", "git_path")
        newenv = {}
        if env:
            for (key, value) in env:
                newenv[key] = value
        if newenv.has_key("PATH"):
            newenv["PATH"] = "%s:%s" % (git_path, newenv["PATH"])
        else:
            newenv["PATH"] = git_path
        return newenv

    def gitcommand(self, command, **kwargs):
        git = self.config.get("broker", "git")
        if isinstance(command, list):
            args = command[:]
        else:
            args = [command]
        args.insert(0, git)
        env = {}
        if kwargs.has_key("env"):
            env = self.gitenv(kwargs.pop("env"))
        p = Popen(args, stdout=PIPE, stderr=PIPE, env=env, **kwargs)
        (out, err) = p.communicate()
        # Ignore out/err unless we get a non-zero return code, then log it.
        self.assertEqual(p.returncode, 0,
                "Non-zero return code for %s, STDOUT:\n@@@\n'%s'\n@@@\nSTDERR:\n@@@\n'%s'\n@@@\n"
                % (command, out, err))
        return


#if __name__=='__main__':

