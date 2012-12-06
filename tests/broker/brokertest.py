# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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
import time
import unittest
from subprocess import Popen, PIPE
import re

from aquilon.config import Config
from aquilon.worker import depends # fetch protobuf, ipaddr dependency

from ipaddr import IPv4Network, IPv4Address

LOCK_RE = re.compile(r'^(acquired|releasing) '
                     r'((compile|delete|sync) )?lock[^\n]*\n', re.M)

DSDB_EXPECT_SUCCESS_FILE = "expected_dsdb_cmds"
DSDB_EXPECT_FAILURE_FILE = "fail_expected_dsdb_cmds"
DSDB_EXPECT_FAILURE_ERROR = "fail_expected_dsdb_error"
DSDB_ISSUED_CMDS_FILE = "issued_dsdb_cmds"


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
                  'aqddnsdomains_pb2', 'aqdlocations_pb2', 'aqdaudit_pb2',
                  'aqdparamdefinitions_pb2', 'aqdparameters_pb2']:
            globals()[m] = __import__(m)

        self.user = self.config.get("broker", "user")
        self.sandboxdir = os.path.join(self.config.get("broker",
                                                       "templatesdir"),
                                       self.user)


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
        self.gzip_profiles = self.config.getboolean("panc", "gzip_output")
        self.profile_suffix = ".xml.gz" if self.gzip_profiles else ".xml"

        dsdb_coverage_dir = os.path.join(self.config.get("unittest", "scratchdir"),
                                         "dsdb_coverage")
        for name in [DSDB_EXPECT_SUCCESS_FILE, DSDB_EXPECT_FAILURE_FILE,
                     DSDB_ISSUED_CMDS_FILE, DSDB_EXPECT_FAILURE_ERROR]:
            path = os.path.join(dsdb_coverage_dir, name)
            try:
                os.remove(path)
            except OSError:
                pass

    def tearDown(self):
        pass

    msversion_dev_re = re.compile('WARNING:msversion:Loading \S* from dev\n')

    def runcommand(self, command, auth=True, **kwargs):
        aq = os.path.join(self.config.get("broker", "srcdir"), "bin", "aq.py")
        if auth:
            port = self.config.get("broker", "kncport")
        else:
            port = self.config.get("broker", "openport")
        if isinstance(command, list):
            args = [str(cmd) for cmd in command]
        else:
            args = [command]
        args.insert(0, sys.executable)
        args.insert(1, aq)
        args.append("--aqport")
        args.append(port)
        if auth:
            args.append("--aqservice")
            args.append(self.config.get("broker", "service"))
        else:
            args.append("--noauth")
        if kwargs.has_key("env"):
            # Make sure that kerberos tickets are still present if the
            # environment is being overridden...
            env = {}
            for (key, value) in kwargs["env"].items():
                env[key] = value
            for (key, value) in os.environ.items():
                if key.find("KRB") == 0 and key not in env:
                    env[key] = value
            if 'USER' not in env:
                env['USER'] = os.environ.get('USER', '')
            kwargs["env"] = env
        p = Popen(args, stdout=PIPE, stderr=PIPE, **kwargs)
        (out, err) = p.communicate()
        # Strip any msversion dev warnings out of STDERR
        err = self.msversion_dev_re.sub('', err)
        # Lock messages are pretty common...
        err = err.replace('Client status messages disabled, '
                          'retries exceeded.\n', '')
        err = LOCK_RE.sub('', err)
        return (p, out, err)

    def successtest(self, command, **kwargs):
        (p, out, err) = self.runcommand(command, **kwargs)
        self.assertEqual(p.returncode, 0,
                         "Non-zero return code for %s, "
                         "STDOUT:\n@@@\n'%s'\n@@@\n"
                         "STDERR:\n@@@\n'%s'\n@@@\n"
                         % (command, out, err))
        return (out, err)

    def statustest(self, command, **kwargs):
        (out, err) = self.successtest(command, **kwargs)
        self.assertEmptyOut(out, command)
        return err

    def failuretest(self, command, returncode, **kwargs):
        (p, out, err) = self.runcommand(command, **kwargs)
        self.assertEqual(p.returncode, returncode,
                         "Non-%s return code %s for %s, "
                         "STDOUT:\n@@@\n'%s'\n@@@\n"
                         "STDERR:\n@@@\n'%s'\n@@@\n"
                         % (returncode, p.returncode, command, out, err))
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
            self.failUnless(err.find("Not Found") >= 0,
                            "STDERR for %s did not include Not Found:"
                            "\n@@@\n'%s'\n@@@\n" %
                            (command, err))
        return err

    def badrequesttest(self, command, ignoreout=False, **kwargs):
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
        if not ignoreout and "--debug" not in command:
            self.assertEqual(out, "",
                             "STDOUT for %s was not empty:\n@@@\n'%s'\n@@@\n" %
                             (command, out))
        return err

    def unauthorizedtest(self, command, auth=False, msgcheck=True, **kwargs):
        (p, out, err) = self.runcommand(command, auth=auth, **kwargs)
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
        if msgcheck:
            self.searchoutput(err, r"Unauthorized (anonymous )?access attempt",
                              command)
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

    def partialerrortest(self, command, **kwargs):
        # Currently these two cases behave the same way - same exit code
        # and behavior.
        return self.badoptiontest(command, **kwargs)

    def matchoutput(self, out, s, command):
        self.assert_(out.find(s) >= 0,
                     "output for %s did not include '%s':\n@@@\n'%s'\n@@@\n" %
                     (command, s, out))

    def matchclean(self, out, s, command):
        self.assert_(out.find(s) < 0,
                     "output for %s includes '%s':\n@@@\n'%s'\n@@@\n" %
                     (command, s, out))

    def searchoutput(self, out, r, command):
        if isinstance(r, str):
            m = re.search(r, out, re.MULTILINE)
        else:
            m = re.search(r, out)
        self.failUnless(m,
                        "output for %s did not match '%s':\n@@@\n'%s'\n@@@\n"
                        % (command, r, out))
        return m

    def searchclean(self, out, r, command):
        if isinstance(r, str):
            m = re.search(r, out, re.MULTILINE)
        else:
            m = re.search(r, out)
        self.failIf(m,
                    "output for %s matches '%s':\n@@@\n'%s'\n@@@\n" %
                    (command, r, out))

    def parse_proto_msg(self, listclass, attr, msg, expect=None):
        protolist = listclass()
        protolist.ParseFromString(msg)
        received = len(getattr(protolist, attr))
        if expect is None:
            self.failUnless(received > 0,
                            "No %s listed in %s protobuf message\n" %
                            (attr, listclass))
        else:
            self.failUnlessEqual(received, expect,
                                 "%d %s expected, got %d\n" %
                                 (expect, attr, received))
        return protolist

    def parse_netlist_msg(self, msg, expect=None):
        return self.parse_proto_msg(aqdnetworks_pb2.NetworkList,
                                    'networks',
                                    msg, expect)

    def parse_hostlist_msg(self, msg, expect=None):
        return self.parse_proto_msg(aqdsystems_pb2.HostList,
                                    'hosts',
                                    msg, expect)

    def parse_clusters_msg(self, msg, expect=None):
        return self.parse_proto_msg(aqdsystems_pb2.ClusterList,
                                    'clusters',
                                    msg, expect)

    def parse_location_msg(self, msg, expect=None):
        return self.parse_proto_msg(aqdlocations_pb2.LocationList,
                                    'locations',
                                    msg, expect)

    def parse_dns_domainlist_msg(self, msg, expect=None):
        return self.parse_proto_msg(aqddnsdomains_pb2.DNSDomainList,
                                    'dns_domains',
                                    msg, expect)

    def parse_service_msg(self, msg, expect=None):
        return self.parse_proto_msg(aqdservices_pb2.ServiceList,
                                    'services',
                                    msg, expect)

    def parse_servicemap_msg(self, msg, expect=None):
        return self.parse_proto_msg(aqdservices_pb2.ServiceMapList,
                                    'servicemaps',
                                    msg, expect)

    def parse_personality_msg(self, msg, expect=None):
        return self.parse_proto_msg(aqdsystems_pb2.PersonalityList,
                                    'personalities',
                                    msg, expect)

    def parse_os_msg(self, msg, expect=None):
        return self.parse_proto_msg(aqdsystems_pb2.OperatingSystemList,
                                    'operating_systems',
                                    msg, expect)

    def parse_audit_msg(self, msg, expect=None):
        return self.parse_proto_msg(aqdaudit_pb2.TransactionList,
                                    'transactions', msg, expect)

    def parse_resourcelist_msg(self, msg, expect=None):
        return self.parse_proto_msg(aqdsystems_pb2.ResourceList,
                                    'resources',
                                    msg, expect)

    def parse_paramdefinition_msg(self, msg, expect=None):
        return self.parse_proto_msg(aqdparamdefinitions_pb2.ParamDefinitionList,
                                    'param_definitions', msg, expect)

    def parse_parameters_msg(self, msg, expect=None):
        return self.parse_proto_msg(aqdparameters_pb2.ParameterList,
                                    'parameters',  msg, expect)
    def gitenv(self, env=None):
        """Configure a known sanitised environment"""
        git_path = self.config.get("broker", "git_path")
        # The "publish" test abuses gitenv(), and it needs the Python interpreter
        # in the path, because it runs the template unit tests which in turn
        # call the aq command
        python_path = os.path.dirname(sys.executable)
        newenv = {}
        newenv["USER"] = os.environ.get('USER', '')
        if env:
            for (key, value) in env.iteritems():
                newenv[key] = value
        if newenv.has_key("PATH"):
            newenv["PATH"] = "%s:%s:%s" % (git_path, python_path, newenv["PATH"])
        else:
            newenv["PATH"] = "%s:%s:%s" % (git_path, python_path, '/bin:/usr/bin')
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
        return (out, err)

    def gitcommand_expectfailure(self, command, **kwargs):
        p = self.gitcommand_raw(command, **kwargs)
        # Ignore out/err unless we get a non-zero return code, then log it.
        (out, err) = p.communicate()
        self.failIfEqual(p.returncode, 0,
                "Zero return code for %s, STDOUT:\n@@@\n'%s'\n@@@\nSTDERR:\n@@@\n'%s'\n@@@\n"
                % (command, out, err))
        return (out, err)

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

    def findcommand(self, command, **kwargs):
        if self.config.has_option("unittest", "find"):
            find = self.config.get("unittest", "find")
        else:
            find = "/usr/bin/find"
        if isinstance(command, list):
            args = command[:]
        else:
            args = [command]
        args.insert(0, find)
        env = {}
        p = Popen(args, stdout=PIPE, stderr=PIPE, **kwargs)
        (out, err) = p.communicate()
        # Ignore out/err unless we get a non-zero return code, then log it.
        if p.returncode == 0:
            return out.splitlines()
        self.fail("Error return code for %s, "
                  "STDOUT:\n@@@\n'%s'\n@@@\nSTDERR:\n@@@\n'%s'\n@@@\n"
                  % (command, out, err))

    def writescratch(self, filename, contents):
        scratchfile = os.path.join(self.scratchdir, filename)
        with open(scratchfile, 'w') as f:
            f.write(contents)
        return scratchfile

    def readscratch(self, filename):
        scratchfile = os.path.join(self.scratchdir, filename)
        with open(scratchfile, 'r') as f:
            contents = f.read()
        return contents

    def dsdb_expect(self, command, fail=False, errstr=""):
        dsdb_coverage_dir = os.path.join(self.config.get("unittest", "scratchdir"),
                                         "dsdb_coverage")
        if fail:
            filename = DSDB_EXPECT_FAILURE_FILE
        else:
            filename = DSDB_EXPECT_SUCCESS_FILE

        expected_name = os.path.join(dsdb_coverage_dir, filename)
        with open(expected_name, "a") as fp:
            if isinstance(command, list):
                fp.write(" ".join([str(cmd) for cmd in command]))
            else:
                fp.write(str(command))
            fp.write("\n")
        if fail and errstr :
            errfile = DSDB_EXPECT_FAILURE_ERROR
            expected_name = os.path.join(dsdb_coverage_dir, errfile)
            with open(expected_name, "a") as fp:
                fp.write(errstr)
                fp.write("\n")

    def dsdb_expect_add(self, hostname, ip, interface=None, mac=None,
                        primary=None, comments=None, fail=False):
        command = ["add_host", "-host_name", hostname,
                   "-ip_address", str(ip), "-status", "aq"]
        if interface:
            command.extend(["-interface_name",
                            str(interface).replace('/', '_')])
        if mac:
            command.extend(["-ethernet_address", str(mac)])
        if primary:
            command.extend(["-primary_host_name", primary])
        if comments:
            command.extend(["-comments", comments])

        self.dsdb_expect(" ".join(command), fail=fail)

    def dsdb_expect_delete(self, ip, fail=False):
        self.dsdb_expect("delete_host -ip_address %s" % ip, fail=fail)

    def dsdb_expect_update(self, fqdn, iface, ip=None, mac=None, comments=None,
                           fail=False):
        command = ["update_aqd_host", "-host_name", fqdn,
                   "-interface_name", iface]
        if ip:
            command.extend(["-ip_address", str(ip)])
        if mac:
            command.extend(["-ethernet_address", str(mac)])
        if comments:
            command.extend(["-comments", comments])
        self.dsdb_expect(" ".join(command), fail=fail)

    def dsdb_expect_update_address(self, fqdn, comments=None, fail=False):
        command = ["update_host", "-host_name", fqdn, "-status", "aq"]
        if comments:
            command.extend(["-comments", comments])
        self.dsdb_expect(" ".join(command), fail=fail)

    def dsdb_expect_rename(self, fqdn, new_fqdn=None, iface=None,
                           new_iface=None, fail=False):
        command = ["update_aqd_host", "-host_name", fqdn]
        if new_fqdn:
            command.extend(["-primary_host_name", new_fqdn])
        if iface:
            command.extend(["-interface_name", iface])
        if new_iface:
            command.extend(["-new_interface_name", new_iface])
        self.dsdb_expect(" ".join(command), fail=fail)

    def dsdb_verify(self, empty=False):
        dsdb_coverage_dir = os.path.join(self.config.get("unittest", "scratchdir"),
                                         "dsdb_coverage")
        fail_expected_name = os.path.join(dsdb_coverage_dir,
                                          DSDB_EXPECT_FAILURE_FILE)
        issued_name = os.path.join(dsdb_coverage_dir, DSDB_ISSUED_CMDS_FILE)

        expected = {}
        for filename in [DSDB_EXPECT_SUCCESS_FILE, DSDB_EXPECT_FAILURE_FILE]:
            expected_name = os.path.join(dsdb_coverage_dir, filename)
            try:
                with open(expected_name, "r") as fp:
                    for line in fp:
                        expected[line.rstrip("\n")] = True
            except IOError:
                pass

        # This is likely a logic error in the test
        if not expected and not empty:
            self.fail("dsdb_verify() called when no DSDB commands were "
                      "expected?!?")

        issued = {}
        try:
            with open(issued_name, "r") as fp:
                for line in fp:
                    issued[line.rstrip("\n")] = True
        except IOError:
            pass

        errors = []
        for cmd, dummy in expected.items():
            if cmd not in issued:
                errors.append("'%s'" % cmd)
        # Unexpected DSDB commands are caught by the fake_dsdb script

        if errors:
            self.fail("The following expected DSDB commands were not called:"
                      "\n@@@\n%s\n@@@\n" % "\n".join(errors))

    def verify_buildfiles(self, domain, object,
                          want_exist=True, command='manage'):
        qdir = self.config.get('broker', 'quattordir')
        domaindir = os.path.join(qdir, 'build', 'xml', domain)
        xmlfile = os.path.join(domaindir, object + self.profile_suffix)
        depfile = os.path.join(domaindir, object + '.xml.dep')
        builddir = self.config.get('broker', 'builddir')
        profile = os.path.join(builddir, 'domains', domain, 'profiles',
                               object + '.tpl')
        for f in [xmlfile, depfile, profile]:
            if want_exist:
                self.failUnless(os.path.exists(f),
                                "Expecting %s to exist before running %s." %
                                (f, command))
            else:
                self.failIf(os.path.exists(f),
                            "Not expecting %s to exist after running %s." %
                            (f, command))

    def demote_current_user(self, role="nobody"):
        principal = self.config.get('unittest', 'principal')
        command = ["permission", "--role", role, "--principal", principal]
        self.noouttest(command)

    def promote_current_user(self):
        srcdir = self.config.get("broker", "srcdir")
        add_admin = os.path.join(srcdir, "tests", "aqdb", "add_admin.py")
        env = os.environ.copy()
        env['AQDCONF'] = self.config.baseconfig
        p = Popen([add_admin], stdout=PIPE, stderr=PIPE, env=env)
        (out, err) = p.communicate()
        self.assertEqual(p.returncode, 0,
                         "Failed to restore admin privs '%s', '%s'." %
                         (out, err))

class DummyIP(IPv4Address):
    def __init__(self, *args, **kwargs):
        super(DummyIP, self).__init__(*args, **kwargs)

        octets = [int(i) for i in str(self).split('.')]
        self.mac = "02:02:%02x:%02x:%02x:%02x" % tuple(octets)

class NetworkInfo(IPv4Network):
    def __init__(self, cidr, nettype):
        super(NetworkInfo, self).__init__(cidr)

        self.nettype = nettype
        self.usable = list()
        self.reserved = list()

        if nettype == 'tor_net':
            offsets = [6, 7]
        elif nettype == 'tor_net2':
            offsets = [7, 8]
        elif nettype == 'vm_storage_net':
            offsets = [39]
        else:
            offsets = []

        for offset in offsets:
            self.reserved.append(DummyIP(self[offset]))

        first_usable = max(offsets or [4]) + 1
        for i in range(first_usable, self.numhosts - 1):
            self.usable.append(DummyIP(self[i]))

    @property
    def gateway(self):
        return self[1]

    def __getitem__(self, idx):
        # Cast the result to DummyIP, so the .mac property can be used
        return DummyIP(super(NetworkInfo, self).__getitem__(idx))


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
        self.tor_net4 = list()
        self.vm_storage_net = list()
        self.vpls = list()
        self.all = list()
        self.unknown.append(NetworkInfo("4.2.1.0/26", "unknown"))
        self.unknown.append(NetworkInfo("4.2.1.64/26", "unknown"))
        self.unknown.append(NetworkInfo("4.2.6.128/29", "unknown"))
        self.unknown.append(NetworkInfo("4.2.6.136/29", "unknown"))
        self.unknown.append(NetworkInfo("4.2.6.144/29", "unknown"))
        self.unknown.append(NetworkInfo("4.2.6.152/29", "unknown"))
        self.unknown.append(NetworkInfo("4.2.6.160/29", "unknown"))
        self.unknown.append(NetworkInfo("4.2.6.168/29", "unknown"))
        self.unknown.append(NetworkInfo("4.2.6.176/29", "unknown"))
        self.unknown.append(NetworkInfo("4.2.6.184/29", "unknown"))
        self.unknown.append(NetworkInfo("4.2.10.0/24", "unknown"))

        # Zebra/bonding/bridge: eth0 address/mac
        self.unknown.append(NetworkInfo("4.2.12.0/26", "unknown"))

        # Zebra/bonding/bridge: eth1 address/mac
        self.unknown.append(NetworkInfo("4.2.12.64/26", "unknown"))

        # Zebra/bonding/bridge: virtual interface addresses
        self.unknown.append(NetworkInfo("4.2.12.128/26", "unknown"))

        # Static routing tests
        self.unknown.append(NetworkInfo("4.2.14.0/25", "unknown"))
        self.unknown.append(NetworkInfo("4.2.14.128/25", "unknown"))

        # Small networks
        self.unknown.append(NetworkInfo("4.2.15.0/32", "unknown"))

        # autopg v2
        self.unknown.append(NetworkInfo("4.2.18.0/29", "unknown"))
        self.unknown.append(NetworkInfo("4.2.18.16/29", "unknown"))

        # Switch loopback
        self.unknown.append(NetworkInfo("4.2.19.0/24", "unknown"))

        # Switch sync testing
        self.unknown.append(NetworkInfo("4.2.20.0/24", "unknown"))

        self.tor_net.append(NetworkInfo("4.2.1.128/26", "tor_net"))
        self.tor_net.append(NetworkInfo("4.2.1.192/26", "tor_net"))
        self.tor_net.append(NetworkInfo("4.2.2.0/26", "tor_net"))
        self.tor_net.append(NetworkInfo("4.2.2.64/26", "tor_net"))
        self.tor_net.append(NetworkInfo("4.2.2.128/26", "tor_net"))
        self.tor_net.append(NetworkInfo("4.2.2.192/26", "tor_net"))
        self.tor_net.append(NetworkInfo("4.2.9.0/26", "tor_net"))
        self.tor_net.append(NetworkInfo("4.2.9.64/26", "tor_net"))
        self.tor_net.append(NetworkInfo("4.2.9.128/26", "tor_net"))
        self.tor_net.append(NetworkInfo("4.2.9.192/26", "tor_net"))
        self.tor_net.append(NetworkInfo("4.2.3.0/25", "tor_net"))
        self.tor_net.append(NetworkInfo("4.2.3.128/25", "tor_net"))
        self.tor_net.append(NetworkInfo("4.2.5.0/25", "tor_net"))
        self.tor_net2.append(NetworkInfo("4.2.4.0/25", "tor_net2"))
        self.tor_net2.append(NetworkInfo("4.2.4.128/25", "tor_net2"))
        self.tor_net2.append(NetworkInfo("4.2.6.192/26", "tor_net2"))
        self.tor_net2.append(NetworkInfo("4.2.7.0/25", "tor_net2"))
        self.tor_net2.append(NetworkInfo("4.2.7.128/25", "tor_net2"))
        self.tor_net2.append(NetworkInfo("4.2.11.0/28", "tor_net2"))
        self.tor_net4.append(NetworkInfo("4.2.8.0/25", "tor_net4"))
        self.vm_storage_net.append(NetworkInfo("4.2.6.0/25", "vm_storage_net"))
        self.vpls.append(NetworkInfo("4.2.13.0/24", "vpls"))
        self.all.extend(self.unknown)
        self.all.extend(self.tor_net)
        self.all.extend(self.tor_net2)
        self.all.extend(self.tor_net4)
        self.all.extend(self.vm_storage_net)
        self.all.extend(self.vpls)

        # network base svc maps, deliberately not in self.all
        self.netsvcmap = NetworkInfo("4.2.16.0/26", "unknown")
        self.netperssvcmap = NetworkInfo("4.2.17.0/26", "unknown")

