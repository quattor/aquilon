# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018  Contributor
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
"""Basic module for running tests on broker commands."""

import pwd
import os
import sys
import unittest
from subprocess import Popen, PIPE
import re
from difflib import unified_diff
from textwrap import dedent

from lxml import etree
from six import string_types

from aquilon.config import Config, lookup_file_path
from aquilon.worker import depends  # pylint: disable=W0611

from aqdb.utils import copy_sqldb

from networktest import DummyNetworks

DSDB_EXPECT_SUCCESS_FILE = "expected_dsdb_cmds"
DSDB_EXPECT_FAILURE_FILE = "fail_expected_dsdb_cmds"
DSDB_EXPECT_FAILURE_ERROR = "fail_expected_dsdb_error"
DSDB_ISSUED_CMDS_FILE = "issued_dsdb_cmds"
CM_JUSTIFICATION = "No justification found, please supply a TCM or SN ticket."
CM_EMERGENCY = "Use of emergency requires a reason to be supplied."
CM_FORMAT = "Failed to parse justification, no valid TCM or SN ticket found."
CM_EDM = "Executing an emergency change without a justification, EDM has not be called."
CM_WARN = 'Continuing with execution; however in the future this operation will fail.'


class TestBrokerCommand(unittest.TestCase):

    config = None
    scratchdir = None
    dsdb_coverage_dir = None
    sandboxdir = None

    user = None
    realm = None

    aurora_with_node = "oy604c2n6"
    aurora_without_node = "pissp1"
    aurora_without_rack = "oy605c2n6"

    valid_just_tcm = ["--justification", "tcm=123456789"]
    exception_trigger_just_tcm = ["--justification", "tcm=666666666"]
    timeout_trigger_just_tcm = ["--justification", "tcm=111111111"]
    timeout_default_trigger_just_tcm = ["--justification", "tcm=222222222"]
    valid_just_sn = ["--justification", "sn=CHNG123456"]
    invalid_justification = ["--justification", "foo"]
    emergency_just_with_reason = ["--justification", "emergency", "--reason", "Valid reason"]
    emergency_tcm_just_with_reason = ["--justification", "emergency,tcm=123456789", "--reason", "Valid reason"]
    emergency_just_without_reason = ["--justification", "emergency"]
    just_reason = ["--reason", "Valid reason"]

    @classmethod
    def setUpClass(cls):
        cls.config = Config()
        cls.net = DummyNetworks(cls.config)

        cls.scratchdir = cls.config.get("unittest", "scratchdir")
        cls.dsdb_coverage_dir = os.path.join(cls.scratchdir, "dsdb_coverage")

        dirs = [cls.scratchdir, cls.dsdb_coverage_dir]
        for dir in dirs:
            if not os.path.exists(dir):
                os.makedirs(dir)

        # Run klist and store the information
        klist = cls.config.lookup_tool('klist')
        p = Popen([klist], stdout=PIPE, stderr=2)
        out, err = p.communicate()
        m = re.search(r'^\s*(?:Default p|P)rincipal:\s*'
                      r'(?P<principal>(?P<user>\S.*)@(?P<realm>.*?))$',
                      out, re.M)
        cls.principal = m.group('principal')
        cls.realm = m.group('realm')

        cls.user = pwd.getpwuid(os.getuid())[0]

        if not cls.user or not cls.realm:
            raise ValueError("Failed to detect the Kerberos principal.")

        cls.sandboxdir = os.path.join(cls.config.get("broker", "templatesdir"),
                                      cls.user)

        cls.template_extension = cls.config.get("panc", "template_extension")
        cls.gzip_profiles = cls.config.getboolean("panc", "gzip_output")
        if cls.gzip_profiles:
            compress_suffix = ".gz"
        else:
            compress_suffix = ""

        cls.xml_suffix = ".xml" + compress_suffix
        cls.xml_default = cls.config.getboolean("panc", "xml_profiles")

        cls.json_suffix = ".json" + compress_suffix
        cls.json_default = cls.config.getboolean("panc", "json_profiles")

        cls.input_xml = etree.parse(lookup_file_path("input.xml"))

        # Need to import protocol buffers after we have the config
        # object all squared away and we can set the sys.path
        # variable appropriately.
        # It would be simpler just to change sys.path in runtests.py,
        # but this allows for each test to be run individually (without
        # the runtests.py wrapper).
        protodir = cls.config.get("protocols", "directory")
        if protodir not in sys.path:
            sys.path.append(protodir)
        cls.protocols = {}
        for m in ['aqdsystems_pb2', 'aqdnetworks_pb2', 'aqdservices_pb2',
                  'aqddnsdomains_pb2', 'aqdlocations_pb2', 'aqdaudit_pb2',
                  'aqdparamdefinitions_pb2', 'aqdparameters_pb2']:
            cls.protocols[m] = __import__(m)

    def setUp(self):
        for name in [DSDB_EXPECT_SUCCESS_FILE, DSDB_EXPECT_FAILURE_FILE,
                     DSDB_ISSUED_CMDS_FILE, DSDB_EXPECT_FAILURE_ERROR]:
            path = os.path.join(self.dsdb_coverage_dir, name)
            try:
                os.remove(path)
            except OSError:
                pass

    def tearDown(self):
        if not os.environ.get("AQD_UNITTEST_FAILFAST"):
            return
        if not all(sys.exc_info()):
            copy_sqldb(self.config, target='SNAPSHOT')

    def template_name(self, *template, **args):
        if args.get("sandbox", None):
            dir = os.path.join(self.sandboxdir, args.get("sandbox"))
        elif args.get("domain", None):
            dir = os.path.join(self.config.get("broker", "domainsdir"),
                               args.get("domain"))
        else:
            self.assertTrue(0, "template_name() called without domain or sandbox")
        return os.path.join(dir, *template) + self.template_extension

    def plenary_name(self, *template):
        dir = self.config.get("broker", "plenarydir")
        return os.path.join(dir, *template) + self.template_extension

    def check_plenary_exists(self, *path):
        plenary = self.plenary_name(*path)
        self.assertTrue(os.path.exists(plenary),
                        "Plenary '%s' does not exist." % plenary)

    def check_plenary_gone(self, *path, **kw):
        plenary = self.plenary_name(*path)
        self.assertFalse(os.path.exists(plenary),
                         "Plenary '%s' was not expected to exist." % plenary)
        if kw.get("directory_gone", False):
            dir = os.path.dirname(plenary)
            self.assertFalse(os.path.exists(dir),
                             "Plenary directory '%s' still exists" % dir)

    def check_plenary_contents(self, *path, **kwargs):
        # Passing lists as a keyword arg triggrest a type error
        contains = kwargs.pop('contains', None)
        clean = kwargs.pop('clean', None)
        if not contains and not clean:
            self.assertTrue(0, "check_plenary_contents called without "
                            "contains or clean")

        self.check_plenary_exists(*path)
        plenary = self.plenary_name(*path)
        with open(plenary) as f:
            contents = f.read()

        if isinstance(contains, list):
            for item in contains:
                self.matchoutput(contents, item, "read %s" % plenary)
        elif contains:
            self.matchoutput(contents, contains, "read %s" % plenary)

        if isinstance(clean, list):
            for item in clean:
                self.matchclean(contents, item, "read %s" % plenary)
        elif clean:
            self.matchclean(contents, clean, "read %s" % plenary)

    def find_template(self, *template, **args):
        """ Figure out the extension of an existing template """
        if args.get("sandbox", None):
            dir = os.path.join(self.sandboxdir, args.get("sandbox"))
        elif args.get("domain", None):
            dir = os.path.join(self.config.get("broker", "domainsdir"),
                               args.get("domain"))
        else:
            self.assertTrue(0, "find_template() called without domain or sandbox")

        base = os.path.join(dir, *template)

        for extension in [".tpl", ".pan"]:
            if os.path.exists(base + extension):
                return base + extension
        self.assertTrue(0, "template %s does not exist with any extension" % base)

    def build_profile_name(self, *template, **args):
        base = os.path.join(self.config.get("broker", "cfgdir"),
                            "domains", args.get("domain"),
                            "profiles", *template)
        return base + self.template_extension

    def tail_file(self, file):
        """
        Get last line from given file
        Assert that line is not empty
        :param file:
        :return:
        """
        with open(file, "r") as f:
            for line in f:
                pass
        self.assertTrue(bool(line.strip()), "Last line is empty")
        return line

    msversion_dev_re = re.compile(r'WARNING:msversion:Loading \S* from dev\n')

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
        if "--aqport" not in args:
            args.append("--aqport")
            args.append(port)
        if auth:
            args.append("--aqservice")
            args.append(self.config.get("broker", "service"))
        else:
            args.append("--noauth")
        if "env" in kwargs:
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
                         "Non-zero return code for %s, "
                         "STDOUT:\n@@@\n'%s'\n@@@\n"
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
                         "Non-zero return code for %s, "
                         "STDOUT:\n@@@\n'%s'\n@@@\n"
                         "STDERR:\n@@@\n'%s'\n@@@\n"
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
            self.assertTrue(err.find("Not Found") >= 0,
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
        self.assertTrue(err.find("Bad Request") >= 0,
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
        self.assertTrue(err.find("Unauthorized:") >= 0,
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

    def deprecatednotimplementederrortest(self, command, **kwargs):
        (p, out, err) = self.runcommand(command, **kwargs)
        err_splited = err.splitlines()
        self.assertEqual(p.returncode, 5,
                         "Return code for %s was %d instead of %d"
                         "\nSTDOUT:\n@@@\n'%s'\n@@@"
                         "\nSTDERR:\n@@@\n'%s'\n@@@" %
                         (command, p.returncode, 5, out, err))
        self.assertEqual(out, "",
                         "STDOUT for %s was not empty:\n@@@\n'%s'\n@@@\n" %
                         (command, out))
        self.assertTrue(
            "Command {} is deprecated".format(command[0]) in err_splited[0],
            "'Command {} is deprecated' not in {}".format(command[0],
                                                          err_splited[0]))
        self.assertTrue(err_splited[1].startswith("Not Implemented"),
                        "STDERR 2nd line for %s did not start with "
                        "Not Implemented:\n@@@\n'%s'\n@@@\n" %
                        (command, err))
        return err

    # Test for conflicting or invalid aq client options.
    def badoptiontest(self, command, exit_code=2, **kwargs):
        (p, out, err) = self.runcommand(command, **kwargs)
        self.assertEqual(p.returncode, exit_code,
                         "Return code for %s was %d instead of %d"
                         "\nSTDOUT:\n@@@\n'%s'\n@@@"
                         "\nSTDERR:\n@@@\n'%s'\n@@@" %
                         (command, p.returncode, exit_code, out, err))
        self.assertEqual(out, "",
                         "STDOUT for %s was not empty:\n@@@\n'%s'\n@@@\n" %
                         (command, out))
        return err

    def justificationmissingtest(self, command, **kwargs):
        out = self.unauthorizedtest(command, **kwargs)
        self.matchoutput(out, CM_JUSTIFICATION, command)

    def reasonmissingtest(self, command, **kwargs):
        out = self.unauthorizedtest(command, **kwargs)
        self.matchoutput(out, CM_EMERGENCY, command)

    def justificationformattest(self, command, **kwargs):
        out = self.unauthorizedtest(command, **kwargs)
        self.matchoutput(out, CM_FORMAT, command)

    def emergencynojustification(self, command, **kwargs):
        (out, err) = self.successtest(command, **kwargs)
        self.matchoutput(err, CM_EDM, command)

    def justificationmissingtest_warn(self, command, **kwargs):
        (out, err) = self.successtest(command, **kwargs)
        self.matchoutput(err, CM_JUSTIFICATION, command)
        self.matchoutput(err, CM_WARN, command)

    def partialerrortest(self, command, **kwargs):
        # Currently these two cases behave the same way - same exit code
        # and behavior.
        return self.badoptiontest(command, **kwargs)

    def matchoutput(self, out, s, command):
        self.assertTrue(out.find(s) >= 0,
                        "output for %s did not include '%s':\n@@@\n'%s'\n@@@\n" %
                        (command, s, out))

    def matchclean(self, out, s, command):
        self.assertTrue(out.find(s) < 0,
                        "output for %s includes '%s':\n@@@\n'%s'\n@@@\n" %
                        (command, s, out))

    def searchoutput(self, out, r, command):
        if isinstance(r, string_types):
            m = re.search(r, out, re.MULTILINE)
        else:
            m = re.search(r, out)
        self.assertTrue(m,
                        "output for %s did not match '%s':\n@@@\n'%s'\n@@@\n"
                        % (command, r, out))
        return m

    def searchclean(self, out, r, command):
        if isinstance(r, string_types):
            m = re.search(r, out, re.MULTILINE)
        else:
            m = re.search(r, out)
        self.assertFalse(m,
                         "output for %s matches '%s':\n@@@\n'%s'\n@@@\n" %
                         (command, r, out))

    def output_equals(self, out, s, command):
        # Check if the output is the string 's'. Leading and trailing
        # whitespace, as well as any common indentation, is ignored.
        out = dedent(out).strip()
        s = dedent(s).strip()
        # Calculate the diff only if we have to...
        if out != s:
            diff = unified_diff(s.splitlines(),
                                out.splitlines(),
                                lineterm="",
                                fromfile="Expected output",
                                tofile="Command output")
            self.assertEqual(out, s,
                             "output for %s differs:\n%s"
                             % (command, "\n".join(diff)))

    def parse_proto_msg(self, listclass, attr, msg, expect=None):
        protolist = listclass()
        protolist.ParseFromString(msg)
        received = len(getattr(protolist, attr))
        if expect is None:
            self.assertTrue(received > 0,
                            "No %s listed in %s protobuf message\n" %
                            (attr, listclass))
        else:
            self.assertEqual(received, expect,
                             "%d %s expected, got %d\n" %
                             (expect, attr, received))
        return getattr(protolist, attr)

    def protobuftest(self, command, expect=None, **kwargs):
        self.assertTrue(isinstance(command, list),
                        "protobuftest() needs the command passed as a list")

        # Extract the command name
        cmd_name = command[0]
        for part in command[1:]:
            if part.startswith("-"):
                break
            cmd_name += "_" + part

        nodelist = self.input_xml.xpath("/commandline/command[@name='%s']" %
                                        cmd_name)
        self.assertTrue(nodelist and len(nodelist) == 1,
                        "Command '%s' was not found in input.xml" % cmd_name)
        cmd_node = nodelist[0]
        msg_node = None
        for fmt_node in cmd_node.getiterator("format"):
            if fmt_node.attrib["name"] != "proto":
                continue
            msg_node = fmt_node.find("message_class")
            break

        self.assertTrue(msg_node is not None,
                        "Command %s does not have protobuf support" % cmd_name)

        module_name = msg_node.attrib["module"]
        cls_name = msg_node.attrib["name"]

        msg_cls = getattr(self.protocols[module_name], cls_name)
        field = msg_cls.DESCRIPTOR.fields[0]

        out = self.commandtest(command, **kwargs)
        return self.parse_proto_msg(msg_cls, field.name, out, expect=expect)

    @classmethod
    def gitenv(cls, env=None):
        """Configure a known sanitised environment"""
        # The "publish" test abuses gitenv(), and it needs the Python interpreter
        # in the path, because it runs the template unit tests which in turn
        # call the aq command

        if env:
            newenv = env.copy()
        else:
            newenv = {}

        if "USER" not in newenv:
            newenv["USER"] = os.environ.get('USER', '')

        if "PATH" in newenv:
            path = env["PATH"].split(":")
        else:
            # Some reasonable defaults...
            path = ["/bin", "/usr/bin"]

        # Allow tests running in a CI environment (e.g. travis) to find local git config
        if "HOME" not in newenv:
            newenv["HOME"] = os.environ.get("HOME", "/home/%(USER)s" % newenv)

        # The 'aq' command need to run some external tools, so make sure those
        # will be found
        for exe in [sys.executable,
                    cls.config.lookup_tool("git"),
                    cls.config.lookup_tool("knc")]:
            if exe[0] != "/":
                continue

            dir = os.path.dirname(exe)
            if dir not in path:
                path.insert(0, dir)

        newenv["PATH"] = ":".join(path)
        return newenv

    def gitcommand_raw(self, command, **kwargs):
        if isinstance(command, list):
            args = command[:]
        else:
            args = [command]
        args.insert(0, self.config.lookup_tool("git"))
        env = self.gitenv(kwargs.pop("env", None))

        p = Popen(args, stdout=PIPE, stderr=PIPE, env=env, **kwargs)
        return p

    def gitcommand(self, command, **kwargs):
        p = self.gitcommand_raw(command, **kwargs)
        # Ignore out/err unless we get a non-zero return code, then log it.
        (out, err) = p.communicate()
        self.assertEqual(p.returncode, 0,
                         "Non-zero return code for %s, "
                         "STDOUT:\n@@@\n'%s'\n@@@\n"
                         "STDERR:\n@@@\n'%s'\n@@@\n"
                         % (command, out, err))
        return (out, err)

    def gitcommand_expectfailure(self, command, **kwargs):
        p = self.gitcommand_raw(command, **kwargs)
        # Ignore out/err unless we get a non-zero return code, then log it.
        (out, err) = p.communicate()
        self.assertNotEqual(p.returncode, 0,
                            "Zero return code for %s, "
                            "STDOUT:\n@@@\n'%s'\n@@@\n"
                            "STDERR:\n@@@\n'%s'\n@@@\n"
                            % (command, out, err))
        return (out, err)

    def check_git_merge_health(self, repo):
        command = "merge HEAD"
        self.gitcommand(command.split(" "), cwd=repo)
        return

    def grepcommand(self, command, **kwargs):
        if isinstance(command, list):
            args = command[:]
        else:
            args = [command]
        args.insert(0, self.config.lookup_tool("grep"))
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
        if isinstance(command, list):
            args = command[:]
        else:
            args = [command]
        args.insert(0, self.config.lookup_tool("find"))
        p = Popen(args, stdout=PIPE, stderr=PIPE, **kwargs)
        (out, err) = p.communicate()
        # Ignore out/err unless we get a non-zero return code, then log it.
        if p.returncode == 0:
            return out.splitlines()
        self.fail("Error return code for %s, "
                  "STDOUT:\n@@@\n'%s'\n@@@\nSTDERR:\n@@@\n'%s'\n@@@\n"
                  % (command, out, err))

    def writescratch(self, filename, contents, raw=False):
        scratchfile = os.path.join(self.scratchdir, filename)
        if raw:
            mode = "wb"
        else:
            mode = "w"
        with open(scratchfile, mode) as f:
            f.write(contents)
        return scratchfile

    def readscratch(self, filename, raw=False):
        scratchfile = os.path.join(self.scratchdir, filename)
        if raw:
            mode = "rb"
        else:
            mode = "r"
        with open(scratchfile, mode) as f:
            contents = f.read()
        return contents

    def dsdb_expect(self, command, fail=False, errstr=""):
        if fail:
            filename = DSDB_EXPECT_FAILURE_FILE
        else:
            filename = DSDB_EXPECT_SUCCESS_FILE

        expected_name = os.path.join(self.dsdb_coverage_dir, filename)
        print expected_name

        with open(expected_name, "a") as fp:
            if isinstance(command, list):
                fp.write(" ".join(str(cmd) for cmd in command))
            else:
                fp.write(str(command))
            fp.write("\n")
        if fail and errstr:
            errfile = DSDB_EXPECT_FAILURE_ERROR
            expected_name = os.path.join(self.dsdb_coverage_dir, errfile)
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

    def dsdb_expect_update(self, fqdn, iface=None, ip=None, mac=None,
                           comments=None, fail=False):
        command = ["update_aqd_host", "-host_name", fqdn]
        if iface:
            command.extend(["-interface_name", iface])
        if ip:
            command.extend(["-ip_address", str(ip)])
        if mac:
            command.extend(["-ethernet_address", str(mac)])
        if comments is not None:
            command.extend(["-comments", comments])
        self.dsdb_expect(" ".join(command), fail=fail)

    def dsdb_expect_rename(self, fqdn, new_fqdn=None, iface=None,
                           new_iface=None, fail=False):
        command = ["update_aqd_host", "-host_name", fqdn]
        if new_fqdn:
            command.extend(["-new_host_name", new_fqdn])
        if iface:
            command.extend(["-interface_name", iface])
        if new_iface:
            command.extend(["-new_interface_name", new_iface])
        self.dsdb_expect(" ".join(command), fail=fail)

    def dsdb_expect_add_campus(self, campus, comments=None, fail=False,
                               errstr=""):
        command = ["add_campus_aq", "-campus_name", campus]
        if comments:
            command.extend(["-comments", comments])
        self.dsdb_expect(" ".join(command), fail=fail, errstr=errstr)

    def dsdb_expect_del_campus(self, campus, fail=False, errstr=""):
        command = ["delete_campus_aq", "-campus", campus]
        self.dsdb_expect(" ".join(command), fail=fail, errstr=errstr)

    def dsdb_expect_add_campus_building(self, campus, building, fail=False,
                                        errstr=""):
        command = ["add_campus_building_aq", "-campus_name", campus,
                   "-building_name", building]
        self.dsdb_expect(" ".join(command), fail=fail, errstr=errstr)

    def dsdb_expect_del_campus_building(self, campus, building, fail=False,
                                        errstr=""):
        command = ["delete_campus_building_aq", "-campus_name", campus,
                   "-building_name", building]
        self.dsdb_expect(" ".join(command), fail=fail, errstr=errstr)

    def dsdb_verify(self, empty=False):
        issued_name = os.path.join(self.dsdb_coverage_dir, DSDB_ISSUED_CMDS_FILE)

        expected = {}
        for filename in [DSDB_EXPECT_SUCCESS_FILE, DSDB_EXPECT_FAILURE_FILE]:
            expected_name = os.path.join(self.dsdb_coverage_dir, filename)
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
                          want_exist=True, command='manage',
                          xml=None, json=None):
        buildfiles = []
        exemptfiles = []

        qdir = self.config.get('broker', 'quattordir')
        domaindir = os.path.join(qdir, 'build', domain)

        buildfiles.append(os.path.join(domaindir, object + '.dep'))
        buildfiles.append(self.build_profile_name(object, domain=domain))

        if xml is None:
            xml = self.xml_default
        if json is None:
            json = self.json_default

        if xml:
            buildfiles.append(os.path.join(domaindir, object + self.xml_suffix))
        else:
            exemptfiles.append(os.path.join(domaindir, object + self.xml_suffix))

        if json:
            buildfiles.append(os.path.join(domaindir, object + self.json_suffix))
        else:
            exemptfiles.append(os.path.join(domaindir, object + self.json_suffix))

        for f in buildfiles:
            if want_exist:
                self.assertTrue(os.path.exists(f),
                                "Expecting %s to exist before running %s." %
                                (f, command))
            else:
                self.assertFalse(os.path.exists(f),
                                 "Not expecting %s to exist after running %s." %
                                 (f, command))

        for f in exemptfiles:
            self.assertFalse(os.path.exists(f),
                             "Not expecting %s to exist after running %s." %
                             (f, command))

    def demote_current_user(self, role="nobody"):
        command = ["permission", "--role", role,
                   "--principal", "%s@%s" % (self.user, self.realm)] + self.valid_just_sn
        self.noouttest(command)

    def promote_current_user(self):
        srcdir = self.config.get("broker", "srcdir")
        set_role = os.path.join(srcdir, "sbin", "aqdb_set_role.py")
        env = os.environ.copy()
        env['AQDCONF'] = self.config.baseconfig
        p = Popen([set_role, '--role', 'aqd_admin'],
                  stdout=PIPE, stderr=PIPE, env=env)
        (out, err) = p.communicate()
        self.assertEqual(p.returncode, 0,
                         "Failed to restore admin privs '%s', '%s'." %
                         (out, err))

    def assertTruedeprecation(self, depr_str, testfunc):
        with open(self.config.get("broker", "logfile"), "r") as logfile:
            # Let's seek to the end of it, matching only against the relevant part.
            logfile.seek(0, 2)
            # Now call the function that should generate the deprecation warning
            testfunc()
            self.assertTrue(elem for elem in logfile if depr_str in elem)

    @staticmethod
    def dynname(ip, domain="aqd-unittest.ms.com"):
        return "dynamic-%s.%s" % (str(ip).replace(".", "-"), domain)
