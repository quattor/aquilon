#!/usr/bin/env python2.5
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
"""This sets up and runs the broker unit tests."""

from __future__ import with_statement

import os
import sys
import getopt
import unittest
import re
from subprocess import Popen

BINDIR = os.path.dirname(os.path.realpath(__file__))
SRCDIR = os.path.join(BINDIR, "..")
sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))


from aquilon.config import Config
from aquilon.utils  import kill_from_pid_file

from broker.orderedsuite import BrokerTestSuite
from aqdb.orderedsuite import DatabaseTestSuite

default_configfile = os.path.join(BINDIR, "unittest.conf")

def usage():
    print >>sys.stderr, """
    %s [--help] [--debug] [--config=configfile]

    --help      returns this message
    --debug     enable debug (not implemented)
    --config    supply an alternate config file
    --coverage  generate code coverage metrics for the broker
                in logs/aqd.coverage.

    Note that:
    %s
    will be used by default, and setting the AQDCONF environment variable
    will *not* work to pass in a config.
    """ % (sys.argv[0], default_configfile)

def force_yes(msg):
    print >>sys.stderr, msg
    print >>sys.stderr, """
        Please confirm by typing yes (three letters) and pressing enter.
        """
    answer = sys.stdin.readline()
    if not answer.startswith("yes"):
        print >>sys.stderr, """Aborting."""
        sys.exit(1)

try:
    opts, args = getopt.getopt(sys.argv[1:], "hdc:vq",
                               ["help", "debug", "config=", "coverage",
                                "verbose", "quiet"])
except getopt.GetoptError, e:
    print >>sys.stderr, str(e)
    usage()
    sys.exit(2)

configfile = default_configfile
coverage = False
verbosity = 1
for o, a in opts:
    if o in ("-h", "--help"):
        usage()
        sys.exit()
    elif o in ("-d", "--debug"):
        # ?
        debug = True
    elif o in ("-c", "--config"):
        configfile = a
    elif o in ("--coverage"):
        coverage = True
    elif o in ("-v", "--verbose"):
        verbosity += 1
    elif o in ("-q", "--quiet"):
        verbosity -= 1
    else:
        assert False, "unhandled option"

if not os.path.exists(configfile):
    print >>sys.stderr, "configfile %s does not exist" % configfile
    sys.exit(1)

if os.environ.get("AQDCONF") and (os.path.realpath(configfile)
        != os.path.realpath(os.environ["AQDCONF"])):
    force_yes("""Will ignore AQDCONF variable value:
%s
and use
%s
instead.""" % (os.environ["AQDCONF"], configfile))

config = Config(configfile=configfile)
if not config.has_section("unittest"):
    config.add_section("unittest")
if not config.has_option("unittest", "srcdir"):
    config.set("unittest", "srcdir", SRCDIR)
if coverage:
    config.set("unittest", "coverage", "True")

makefile = os.path.join(SRCDIR, "Makefile")
prod_python = None
with open(makefile) as f:
    prod_python_re = re.compile(r'^PYTHON\s*=\s*(.*?)\s*$')
    for line in f.readlines():
        m = prod_python_re.search(line)
        if m:
            prod_python = m.group(1)
            break
# Another approach would be to exec prod_python with
# -c 'import platform; print platform.python_version()' and then compare
# with the current running python_version.
if prod_python and sys.executable.find(prod_python) < 0:
    print "\n"
    force_yes("Running with %s but prod is %s" % (sys.executable, prod_python))

production_database = "NYPO_AQUILON"
if (config.get("database", "vendor") == "oracle" and
        config.get("database", "server") == production_database):
    force_yes("About to run against the production database %s" %
            production_database)

# Maybe just execute this every run...
if not os.path.exists("/var/spool/keytabs/%s" % config.get("broker", "user")):
    p = Popen(("/ms/dist/kerberos/PROJ/krb5_keytab/prod/sbin/krb5_keytab"),
            stdout=1, stderr=2)
    rc = p.wait()

pid_file = os.path.join(config.get('broker', 'rundir') , 'aqd.pid')
kill_from_pid_file(pid_file)

for label in ["quattordir", "kingdir", "swrepdir", ]:
    dir = config.get("broker", label)
    if os.path.exists(dir):
        continue
    try:
        os.makedirs(dir)
    except OSError, e:
        print >>sys.stderr, "Could not create %s: %s" % (dir, e)

dirs = [config.get("database", "dbdir"), config.get("unittest", "scratchdir")]
for label in ["templatesdir", "rundir", "logdir", "profilesdir",
        "depsdir", "hostsdir", "plenarydir", ]:
    dirs.append(config.get("broker", label))

if configfile != default_configfile:
    force_yes(
        "About to remove any of the following directories that exist:\n%s\n"
        % "\n".join(dirs))

for dir in dirs:
    if os.path.exists(dir):
        print "Removing %s" % dir
        p = Popen(("/bin/rm", "-rf", dir), stdout=1, stderr=2)
        rc = p.wait()
        # FIXME: check rc
    try:
        os.makedirs(dir)
    except OSError, e:
        print >>sys.stderr, "Could not create %s: %s" % (dir, e)

# The template-king also gets synced as part of the broker tests,
# but this makes it available for the initial database build.
# This syncs the *contents* of the remote "template-king" by
# appending a slash, so the remote could be any path that rsync
# can parse that leads to a git repository.
p = Popen(("rsync", "-avP", "-e", "ssh", "--delete",
           "--exclude=.git/config",
           os.path.join(config.get("unittest", "template_king_path"), ""),
           config.get("broker", "kingdir")),
          stdout=1, stderr=2)
rc = p.wait()
# FIXME: check rc
# Need the actual king's config file for merges to work.
p = Popen(("rsync", "-avP", "-e", "ssh",
           config.get("unittest", "template_king_config"),
           os.path.join(config.get("broker", "kingdir"), ".git")),
          stdout=1, stderr=2)
rc = p.wait()
# FIXME: check rc

swrep_repository_host = config.get("unittest", "swrep_repository_host")
# The swrep/repository is currently *only* synced here at the top level.
p = Popen(("rsync", "-avP", "-e", "ssh", "--delete",
    "%s:/var/quattor/swrep/repository" % swrep_repository_host,
    config.get("broker", "swrepdir")),
    stdout=1, stderr=2)
rc = p.wait()
# FIXME: check rc


class VerboseTextTestResult(unittest._TextTestResult):
    lastmodule = ""

    def printModule(self, test):
        if self.dots:
            if test.__class__.__module__ != self.lastmodule:
                self.lastmodule = test.__class__.__module__
                self.stream.writeln("")
                self.stream.write("%s" % self.lastmodule)

    def addSuccess(self, test):
        self.printModule(test)
        unittest._TextTestResult.addSuccess(self, test)

    def printResult(self, flavour, result):
        (test, err) = result
        self.stream.writeln()
        self.stream.writeln(self.separator1)
        self.stream.writeln("%s: %s" % (flavour, self.getDescription(test)))
        self.stream.writeln(self.separator2)
        self.stream.writeln("%s" % err)

    def addError(self, test, err):
        self.printModule(test)
        # Specifically skip over base class's implementation.
        unittest.TestResult.addError(self, test, err)
        self.printResult("ERROR", self.errors[-1])

    def addFailure(self, test, err):
        self.printModule(test)
        # Specifically skip over base class's implementation.
        unittest.TestResult.addFailure(self, test, err)
        self.printResult("FAIL", self.failures[-1])


class VerboseTextTestRunner(unittest.TextTestRunner):
    def _makeResult(self):
        return VerboseTextTestResult(self.stream, self.descriptions,
                                     self.verbosity)


suite = unittest.TestSuite()
# Relies on the oracle rebuild doing a nuke first.
suite.addTest(DatabaseTestSuite())
suite.addTest(BrokerTestSuite())
VerboseTextTestRunner(verbosity=verbosity).run(suite)
