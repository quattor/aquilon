# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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
        self.net = DummyNetworks()

        # Need to import protocol buffers after we have the config
        # object all squared away and we can set the sys.path
        # variable appropriately.
        # It would be simpler just to change sys.path in runtests.py,
        # but this allows for each test to be run individually (without
        # the runtests.py wrapper).
        protodir = self.config.get("protocols", "directory")
        if protodir not in sys.path:
            sys.path.append(protodir)
        for m in ['aqdsystems_pb2', 'aqdnetworks_pb2', 'aqdservices_pb2',
                  'aqddnsdomains_pb2']:
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

    def tearDown(self):
        pass

    msversion_dev_re = re.compile('WARNING:msversion:Loading \S* from dev\n')

    def runcommand(self, command, **kwargs):
        aq = os.path.join(self.config.get("broker", "srcdir"), "bin", "aq.py")
        kncport = self.config.get("broker", "kncport")
        if isinstance(command, list):
            args = command[:]
        else:
            args = [command]
        args.insert(0, sys.executable)
        args.insert(1, aq)
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
        # Lock messages are pretty common...
        err = err.replace('requesting compile lock\n', '')
        err = err.replace('acquired compile lock\n', '')
        err = err.replace('releasing compile lock\n', '')
        return (p, out, err)

    def successtest(self, command, **kwargs):
        (p, out, err) = self.runcommand(command, **kwargs)
        self.assertEqual(p.returncode, 0,
                         "Non-zero return code for %s, "
                         "STDOUT:\n@@@\n'%s'\n@@@\n"
                         "STDERR:\n@@@\n'%s'\n@@@\n"
                         % (command, out, err))
        return (out, err)

    def assertEmptyStream(self, name, contents, command):
        self.assertEqual(contents, "",
                         "%s for %s was not empty:\n@@@\n'%s'\n@@@\n"
                         % (name, command, contents))

    def assertEmptyErr(self, contents, command):
        self.assertEmptyStream("STDERR", contents, command)

    def assertEmptyOut(self, contents, command):
        self.assertEmptyStream("STDOUT", contents, command)

    def commandtest(self, command, **kwargs):
        (p, out, err) = self.runcommand(command, **kwargs)
        self.assertEmptyErr(err, command)
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
                             "\n@@@\n'%s'\n@@@\n" % (command, err))
        return err

    def badrequesttest(self, command, **kwargs):
        (p, out, err) = self.runcommand(command, **kwargs)
        self.assertEqual(p.returncode, 4,
                         "Return code for %s was %d instead of %d"
                         "\nSTDOUT:\n@@@\n'%s'\n@@@"
                         "\nSTDERR:\n@@@\n'%s'\n@@@" %
                         (command, p.returncode, 4, out, err))
        self.failUnless(err.find("Bad Request") >= 0,
                        "STDERR for %s did not include Bad Request:"
                        "\n@@@\n'%s'\n@@@\n" %
                        (command, err))
        if "--debug" not in command:
            self.assertEqual(out, "",
                             "STDOUT for %s was not empty:\n@@@\n'%s'\n@@@\n" %
                             (command, out))
        return err

    def unauthorizedtest(self, command, **kwargs):
        aq = os.path.join(self.config.get("broker", "srcdir"), "bin", "aq.py")
        openport = self.config.get("broker", "openport")
        if isinstance(command, list):
            args = command[:]
        else:
            args = [command]
        args.insert(0, sys.executable)
        args.insert(1, aq)
        args.append("--aqport")
        args.append(openport)
        args.append("--noauth")
        p = Popen(args, stdout=PIPE, stderr=PIPE, **kwargs)
        (out, err) = p.communicate()
        # Strip any msversion dev warnings out of STDERR
        err = self.msversion_dev_re.sub('', err)
        self.assertEqual(p.returncode, 4,
                         "Return code for %s was %d instead of %d"
                         "\nSTDOUT:\n@@@\n'%s'\n@@@"
                         "\nSTDERR:\n@@@\n'%s'\n@@@" %
                         (command, p.returncode, 4, out, err))
        self.assertEqual(out, "",
                         "STDOUT for %s was not empty:\n@@@\n'%s'\n@@@\n" %
                         (command, out))
        self.failUnless(err.find("Unauthorized:") >= 0,
                        "STDERR for %s did not include Unauthorized:"
                        "\n@@@\n'%s'\n@@@\n" %
                        (command, err))
        self.matchoutput(err, "Unauthorized anonymous access attempt", command)
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

    def unimplementederrortest(self, command, **kwargs):
        (p, out, err) = self.runcommand(command, **kwargs)
        self.assertEqual(p.returncode, 5,
                         "Return code for %s was %d instead of %d"
                         "\nSTDOUT:\n@@@\n'%s'\n@@@"
                         "\nSTDERR:\n@@@\n'%s'\n@@@" %
                         (command, p.returncode, 5, out, err))
        self.assertEqual(out, "",
                         "STDOUT for %s was not empty:\n@@@\n'%s'\n@@@\n" %
                         (command, out))
        self.assertEqual(err.find("Not Implemented"), 0,
                         "STDERR for %s did not start with "
                         "Not Implemented:\n@@@\n'%s'\n@@@\n" %
                         (command, err))
        return err

    # Test for conflicting or invalid aq client options.
    def badoptiontest(self, command, **kwargs):
        (p, out, err) = self.runcommand(command, **kwargs)
        self.assertEqual(p.returncode, 2,
                         "Return code for %s was %d instead of %d"
                         "\nSTDOUT:\n@@@\n'%s'\n@@@"
                         "\nSTDERR:\n@@@\n'%s'\n@@@" %
                         (command, p.returncode, 2, out, err))
        self.assertEqual(out, "",
                         "STDOUT for %s was not empty:\n@@@\n'%s'\n@@@\n" %
                         (command, out))
        return err

    def matchoutput(self, out, s, command):
        self.assert_(out.find(s) >= 0,
                     "output for %s did not include '%s':\n@@@\n'%s'\n@@@\n" %
                     (command, s, out))

    def matchclean(self, out, s, command):
        self.assert_(out.find(s) < 0,
                     "output for %s includes '%s':\n@@@\n'%s'\n@@@\n" %
                     (command, s, out))

    def searchoutput(self, out, r, command):
        m = re.search(r, out)
        self.failUnless(m,
                        "output for %s did not match '%s':\n@@@\n'%s'\n@@@\n"
                        % (command, r, out))
        return m

    def searchclean(self, out, r, command):
        self.failIf(re.search(r, out),
                    "output for %s matches '%s':\n@@@\n'%s'\n@@@\n" %
                    (command, r, out))

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

    def parse_dns_domainlist_msg(self, msg, expect=None):
        dns_domainlist = aqddnsdomains_pb2.DNSDomainList()
        dns_domainlist.ParseFromString(msg)
        received = len(dns_domainlist.dns_domains)
        if expect is None:
            self.failUnless(received > 0,
                            "No DNS domains listed in DNSDomainList "
                            "protobuf message\n")
        else:
            self.failUnlessEqual(received, expect,
                                 "%d DNS domain(s) expected, got %d\n" %
                                 (expect, received))
        return dns_domainlist

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

    def parse_personality_msg(self, msg, expect=None):
        personalitylist = aqdsystems_pb2.PersonalityList()
        personalitylist.ParseFromString(msg)
        received = len(personalitylist.personalities)
        if expect is None:
            self.failUnless(received > 0,
                            "No personalities listed in PersonalityList "
                            "protobuf message\n")
        else:
            self.failUnlessEqual(received, expect,
                                 "%d personalities expected, got %d\n" %
                                 (expect, received))
        return personalitylist

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

    def gitcommand_raw(self, command, **kwargs):
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
        return p

    def gitcommand(self, command, **kwargs):
        p = self.gitcommand_raw(command, **kwargs)
        # Ignore out/err unless we get a non-zero return code, then log it.
        (out, err) = p.communicate()
        self.assertEqual(p.returncode, 0,
                "Non-zero return code for %s, STDOUT:\n@@@\n'%s'\n@@@\nSTDERR:\n@@@\n'%s'\n@@@\n"
                % (command, out, err))
        return

    def gitcommand_expectfailure(self, command, **kwargs):
        p = self.gitcommand_raw(command, **kwargs)
        # Ignore out/err unless we get a non-zero return code, then log it.
        (out, err) = p.communicate()
        self.assertEqual(p.returncode, 1,
                "Zero return code for %s, STDOUT:\n@@@\n'%s'\n@@@\nSTDERR:\n@@@\n'%s'\n@@@\n"
                % (command, out, err))
        return err

    def check_git_merge_health(self, repo):
        command = "merge HEAD"
        out = self.gitcommand(command.split(" "), cwd=repo)
        return

    def grepcommand(self, command, **kwargs):
        if self.config.has_option("unittest", "grep"):
            grep = self.config.get("unittest", "grep")
        else:
            grep = "/bin/grep"
        if isinstance(command, list):
            args = command[:]
        else:
            args = [command]
        args.insert(0, grep)
        env = {}
        p = Popen(args, stdout=PIPE, stderr=PIPE, **kwargs)
        (out, err) = p.communicate()
        # Ignore out/err unless we get a non-zero return code, then log it.
        if p.returncode == 0:
            return out.splitlines()
        if p.returncode == 1:
            return []
        self.fail("Error return code for %s, "
                  "STDOUT:\n@@@\n'%s'\n@@@\nSTDERR:\n@@@\n'%s'\n@@@\n"
                  % (command, out, err))


class DummyIP(object):
    def __init__(self, parts):
        self.ip = ".".join([str(i) for i in parts])
        self.mac = "02:02:%02x:%02x:%02x:%02x" % parts


class NetworkInfo(object):
    def __init__(self, ip, mask, nettype):
        # Currently only good for mask in [64, 128].
        self.ip = ip
        self.mask = mask
        self.nettype = nettype
        parts = ip.split(".")
        gateway = [int(i) for i in parts]
        broadcast = gateway[:]
        gateway[3] += 1
        broadcast[3] = broadcast[3] + mask - 1
        # Assumes gateway is first and broadcast is last.
        self.gateway = ".".join([str(i) for i in gateway])
        self.broadcast = ".".join([str(i) for i in broadcast])

        if self.mask == 64:
            self.netmask = "255.255.255.192"
        elif self.mask == 128:
            self.netmask = "255.255.255.128"

        if nettype == 'tor_net':
            offsets = [6, 7]
        elif nettype == 'tor_net2':
            offsets = [7, 8]
        else:
            offsets = []

        self.usable = list()
        self.reserved = list()
        usable_start = gateway[3] + 1
        for offset in offsets:
            reserved = gateway[:]
            reserved[3] = gateway[3] - 1 + offset
            usable_start = reserved[3] + 1
            self.reserved.append(DummyIP(tuple(reserved)))
        for i in range(usable_start, broadcast[3]):
            newip = gateway[:]
            newip[3] = i
            self.usable.append(DummyIP(tuple(newip)))


class DummyNetworks(object):
    # Borg
    __shared_state = {}

    def __init__(self, *args, **kwargs):
        self.__dict__ = self.__shared_state
        if getattr(self, "unknown", None):
            return
        object.__init__(self, *args, **kwargs)
        self.unknown = list()
        self.tor_net = list()
        self.tor_net2 = list()
        self.all = list()
        self.unknown.append(NetworkInfo("4.2.1.0", 64, "unknown"))
        self.unknown.append(NetworkInfo("4.2.1.64", 64, "unknown"))
        self.tor_net.append(NetworkInfo("4.2.1.128", 64, "tor_net"))
        self.tor_net.append(NetworkInfo("4.2.1.192", 64, "tor_net"))
        self.tor_net.append(NetworkInfo("4.2.2.0", 64, "tor_net"))
        self.tor_net.append(NetworkInfo("4.2.2.64", 64, "tor_net"))
        self.tor_net.append(NetworkInfo("4.2.2.128", 64, "tor_net"))
        self.tor_net.append(NetworkInfo("4.2.2.192", 64, "tor_net"))
        self.tor_net.append(NetworkInfo("4.2.3.0", 128, "tor_net"))
        self.tor_net.append(NetworkInfo("4.2.3.128", 128, "tor_net"))
        self.tor_net2.append(NetworkInfo("4.2.4.0", 128, "tor_net2"))
        self.tor_net2.append(NetworkInfo("4.2.4.128", 128, "tor_net2"))
        self.all.extend(self.unknown)
        self.all.extend(self.tor_net)
        self.all.extend(self.tor_net2)
