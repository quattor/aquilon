# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
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

import ms.version
ms.version.addpkg('setuptools', '0.6c8-py25')
ms.version.addpkg('protoc', 'prod', meta='aquilon')


class TestBrokerCommand(unittest.TestCase):

    def setUp(self):
        self.config = Config()

        # Need to import protocol buffers after we have the config
        # object all squared away and we can set the sys.path
        # variable appropriately.
        # It would be simpler just to change sys.path in runtests.py,
        # but this allows for each test to be run individually (without
        # the runtests.py wrapper).
        protodir = self.config.get("protocols", "directory")
        if protodir not in sys.path:
            sys.path.append(protodir)
        for m in ['aqdsystems_pb2', 'aqdnetworks_pb2', 'aqdservices_pb2']:
            globals()[m] = __import__(m)

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
            self.aurora_without_node = "pissp1"
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
        self.hostip6 = "8.8.5.253"
        self.hostmac6 = "02:02:08:08:05:fd"
        self.hostip7 = "8.8.5.254"
        self.hostmac7 = "02:02:08:08:05:fe"
        self.hostip8 = "8.8.6.251"
        self.hostmac8 = "02:02:08:08:06:fb"
        self.hostip9 = "8.8.6.252"
        self.hostmac9 = "02:02:08:08:06:fc"
        self.hostip10 = "8.8.6.253"
        self.hostmac10 = "02:02:08:08:06:fd"
        self.hostip11 = "8.8.6.254"
        self.hostmac11 = "02:02:08:08:06:ff"
        self.hostip12 = "8.8.7.251"
        self.hostmac12 = "02:02:08:08:07:fb"
        self.hostip13 = "8.8.7.252"
        self.hostmac13 = "02:02:08:08:07:fc"
        # This one is special, needs to be second-to-last on the subnet
        self.hostip14 = "8.8.7.253"
        self.hostmac14 = "02:02:08:08:07:fd"
        # This one is special, needs to be last on the subnet before broadcast
        self.hostip15 = "8.8.7.254"
        self.hostmac15 = "02:02:08:08:07:fe"
        # This one may be special... first 'available' on the subnet
        self.hostip16 = "8.8.4.8"
        self.hostmac16 = "02:02:08:08:04:08"
        self.hostip17 = "8.8.4.9"
        self.hostmac17 = "02:02:08:08:04:09"
        # Just define a bunch of generic ones at once...
        for n in range(50, 100):
            setattr(self, "hostip%d" % n, "8.8.5.%d" % (n-50))
            setattr(self, "hostmac%d" % n, "02:02:08:08:05:%02x" % (n-50))
        # Let config settings override any of the above.
        for n in range(100):
            for h in ["hostip", "hostmac", "broadcast", "gateway", "netmask"]:
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
        if p.returncode == 0:
            self.assertEqual(err, "",
                             "STDERR for %s was not empty:\n@@@\n'%s'\n@@@\n" %
                             (command, err))
            self.assertEqual(out, "",
                             "STDOUT for %s was not empty:\n@@@\n'%s'\n@@@\n" %
                             (command, out))
        else:
            self.assertEqual(p.returncode, 4,
                             "Return code for %s was %d instead of %d"
                             "\nSTDOUT:\n@@@\n'%s'\n@@@"
                             "\nSTDERR:\n@@@\n'%s'\n@@@" %
                             (command, p.returncode, 4, out, err))
            self.assertEqual(out, "",
                             "STDOUT for %s was not empty:\n@@@\n'%s'\n@@@\n" %
                             (command, out))
            self.assertEqual(err.find("Not Found"), 0,
                             "STDERR for %s did not start with Not Found:"
                             "\n@@@\n'%s'\n@@@\n" % (command, out))
        return err

    def badrequesttest(self, command, **kwargs):
        (p, out, err) = self.runcommand(command, **kwargs)
        self.assertEqual(p.returncode, 4,
                         "Return code for %s was %d instead of %d"
                         "\nSTDOUT:\n@@@\n'%s'\n@@@"
                         "\nSTDERR:\n@@@\n'%s'\n@@@" %
                         (command, p.returncode, 4, out, err))
        self.assertEqual(out, "",
                         "STDOUT for %s was not empty:\n@@@\n'%s'\n@@@\n" %
                         (command, out))
        self.assertEqual(err.find("Bad Request"), 0,
                         "STDERR for %s did not start with Bad Request:"
                         "\n@@@\n'%s'\n@@@\n" %
                         (command, err))
        return err

    def internalerrortest(self, command, **kwargs):
        (p, out, err) = self.runcommand(command, **kwargs)
        self.assertEqual(p.returncode, 5,
                         "Return code for %s was %d instead of %d"
                         "\nSTDOUT:\n@@@\n'%s'\n@@@"
                         "\nSTDERR:\n@@@\n'%s'\n@@@" %
                         (command, p.returncode, 5, out, err))
        self.assertEqual(out, "",
                         "STDOUT for %s was not empty:\n@@@\n'%s'\n@@@\n" %
                         (command, out))
        self.assertEqual(err.find("Internal Server Error"), 0,
                         "STDERR for %s did not start with "
                         "Internal Server Error:\n@@@\n'%s'\n@@@\n" %
                         (command, err))
        return err

    def matchoutput(self, out, s, command):
        self.assert_(out.find(s) >= 0,
                     "output for %s did not include '%s':\n@@@\n'%s'\n@@@\n" %
                     (command, s, out))

    def matchclean(self, out, s, command):
        self.assert_(out.find(s) < 0,
                     "output for %s includes '%s':\n@@@\n'%s'\n@@@\n" %
                     (command, s, out))

    def parse_netlist_msg(self, msg, expect=None):
        netlist = aqdnetworks_pb2.NetworkList()
        netlist.ParseFromString(msg)
        received = len(netlist.networks)
        if expect is None:
            self.failUnless(received > 0,
                            "No networks listed in NetworkList "
                            "protobuf message\n")
        else:
            self.failUnlessEqual(received, expect,
                                 "%d network(s) expected, got %d\n" %
                                 (expect, received))
        return netlist

    def parse_srvlist_msg(self, msg, expect=None):
        srvlist = aqdservices_pb2.ServiceList()
        srvlist.ParseFromString(msg)
        received = len(srvlist.services)
        if expect is None:
            self.failUnless(received > 0,
                            "No services listed in ServiceList "
                            "protobuf message\n")
        else:
            self.failUnlessEqual(received, expect,
                                 "%d service(s) expected, got %d\n" %
                                 (expect, received))
        return srvlist

    def parse_hostlist_msg(self, msg, expect=None):
        hostlist = aqdsystems_pb2.HostList()
        hostlist.ParseFromString(msg)
        received = len(hostlist.hosts)
        if expect is None:
            self.failUnless(received > 0,
                            "No hosts listed in HostList protobuf message\n")
        else:
            self.failUnlessEqual(received, expect,
                                 "%d host(s) expected, got %d\n" %
                                 (expect, received))
        return hostlist

    def parse_servicemap_msg(self, msg, expect=None):
        servicemaplist = aqdservices_pb2.ServiceMapList()
        servicemaplist.ParseFromString(msg)
        received = len(servicemaplist.servicemaps)
        if expect is None:
            self.failUnless(received > 0,
                            "No service maps listed in ServiceMapList "
                            "protobuf message\n")
        else:
            self.failUnlessEqual(received, expect,
                                 "%d host(s) expected, got %d\n" %
                                 (expect, received))
        return servicemaplist

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


