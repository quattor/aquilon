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
import re

from aquilon.config import Config

class TestBrokerCommand(unittest.TestCase):

    def setUp(self):
        self.config = Config()
        # This method is cumbersome.  Should probably develop something
        # like unittest.conf.defaults.
        if self.config.has_option("unittest", "scratchdir"):
            self.scratchdir = self.config.get("unittest", "scratchdir")
            if not os.path.exists(self.scratchdir):
                os.makedirs(self.scratchdir)
        if self.config.has_option("unittest", "host_not_running_aqd"):
            self.host_not_running_aqd = self.config.get("unittest",
                    "host_not_running_aqd")
        else:
            self.host_not_running_aqd = "nyinfra0"
        if self.config.has_option("unittest", "aurora_with_node"):
            self.aurora_with_node = self.config.get("unittest",
                    "aurora_with_node")
        else:
            self.aurora_with_node = "oyidb1622"
        if self.config.has_option("unittest", "aurora_without_node"):
            self.aurora_without_node = self.config.get("unittest",
                    "aurora_without_node")
        else:
            self.aurora_without_node = "oziyp2"
        # An alternate set of defaults is listed in unittest.conf.
        self.hostip0 = "8.8.4.251"
        self.netmask0 = "255.255.252.0"
        self.broadcast0 = "8.8.7.255"
        self.gateway0 = "8.8.4.1"
        self.hostmac0 = "02:02:08:08:04:fb"
        self.hostip1 = "8.8.4.252"
        self.hostmac1 = "02:02:08:08:04:fc"
        self.hostip2 = "8.8.4.253"
        self.netmask2 = "255.255.252.0"
        self.broadcast2 = "8.8.7.255"
        self.gateway2 = "8.8.4.1"
        self.hostmac2 = "02:02:08:08:04:fd"
        self.hostip3 = "8.8.4.254"
        self.netmask3 = "255.255.252.0"
        self.broadcast3 = "8.8.7.255"
        self.gateway3 = "8.8.4.1"
        self.hostmac3 = "02:02:08:08:04:fe"
        self.hostip4 = "8.8.5.251"
        self.hostmac4 = "02:02:08:08:05:fb"
        self.hostip5 = "8.8.5.252"
        self.hostmac5 = "02:02:08:08:05:fc"
        self.updateip0 = "8.8.5.253"
        self.updatemac0 = "02:02:08:08:05:fd"
        self.updateip1 = "8.8.5.254"
        self.updatemac1 = "02:02:08:08:05:fe"
        for n in range(6):
            for h in ["hostip", "hostmac", "broadcast", "gateway", "netmask",
                    "updateip", "updatemac"]:
                p = "%s%s" % (h, n)
                if self.config.has_option("unittest", p):
                    setattr(self, p, self.config.get("unittest", p))

    def tearDown(self):
        pass

    msversion_dev_re = re.compile('WARNING:msversion:Loading \S* from dev\n')

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
        args.append("--aquser")
        args.append(self.config.get("broker", "user"))
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
        (out, err) = p.communicate()
        # Strip any msversion dev warnings out of STDERR
        err = self.msversion_dev_re.sub('', err)
        return (p, out, err)

    def commandtest(self, command, **kwargs):
        (p, out, err) = self.runcommand(command, **kwargs)
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
        (p, out, err) = self.runcommand(command, **kwargs)
        # Ignore out/err unless we get a non-zero return code, then log it.
        self.assertEqual(p.returncode, 0,
                "Non-zero return code for %s, STDOUT:\n@@@\n'%s'\n@@@\nSTDERR:\n@@@\n'%s'\n@@@\n"
                % (command, out, err))
        return

    # Right now, commands are not implemented consistently.  When that is
    # addressed, this unit test should be updated.
    def notfoundtest(self, command, **kwargs):
        (p, out, err) = self.runcommand(command, **kwargs)
        self.assertEqual(err, "",
                "STDERR for %s was not empty:\n@@@\n'%s'\n@@@\n"
                % (command, err))
        if p.returncode == 0:
            self.assertEqual(out, "",
                    "STDOUT for %s was not empty:\n@@@\n'%s'\n@@@\n"
                    % (command, out))
        else:
            self.assertEqual(p.returncode, 4,
                "Return code for %s was %d instead of %d, STDOUT:\n@@@\n'%s'\n"
                % (command, p.returncode, 4, out))
            self.assertEqual(out.find("Not Found"), 0,
                    "STDOUT for %s did not start with Not Found:\n@@@\n'%s'\n@@@\n"
                    % (command, out))
        return

    def badrequesttest(self, command, **kwargs):
        (p, out, err) = self.runcommand(command, **kwargs)
        self.assertEqual(err, "",
                "STDERR for %s was not empty:\n@@@\n'%s'\n@@@\n"
                % (command, err))
        self.assertEqual(p.returncode, 4,
                "Return code for %s was %d instead of %d, STDOUT:\n@@@\n'%s'\n"
                % (command, p.returncode, 4, out))
        self.assertEqual(out.find("Bad Request"), 0,
                "STDOUT for %s did not start with Bad Request:\n@@@\n'%s'\n@@@\n"
                % (command, out))
        return

    def internalerrortest(self, command, **kwargs):
        (p, out, err) = self.runcommand(command, **kwargs)
        self.assertEqual(err, "",
                "STDERR for %s was not empty:\n@@@\n'%s'\n@@@\n"
                % (command, err))
        self.assertEqual(p.returncode, 5,
                "Return code for %s was %d instead of %d, STDOUT:\n@@@\n'%s'\n"
                % (command, p.returncode, 5, out))
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

