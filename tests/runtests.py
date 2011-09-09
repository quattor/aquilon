#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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


import os
import re
import sys
import getopt
import unittest
from subprocess import Popen

import depends

BINDIR = os.path.dirname(os.path.realpath(__file__))
SRCDIR = os.path.join(BINDIR, "..")
sys.path.append(os.path.join(SRCDIR, "lib", "python2.6"))

from aquilon.config import Config
from aquilon.utils  import kill_from_pid_file
from verbose_text_test import VerboseTextTestRunner

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
                in logs/coverage.
    --profile   generate profile information in logs/aqd.profile

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
    opts, args = getopt.getopt(sys.argv[1:], "hdc:vqm",
                               ["help", "debug", "config=", "coverage",
                                "profile", "verbose", "quiet", "mirror"])
except getopt.GetoptError, e:
    print >>sys.stderr, str(e)
    usage()
    sys.exit(2)

configfile = default_configfile
coverage = False
profile = False
verbosity = 1
mirror = False
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
    elif o in ("--profile"):
        profile = True
    elif o in ("-v", "--verbose"):
        verbosity += 1
    elif o in ("-q", "--quiet"):
        verbosity -= 1
    elif o in ("-m", "--mirror"):
        mirror = True
    else:
        assert False, "unhandled option '%s'" % o

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
if profile:
    config.set("unittest", "profile", "True")

if mirror:
    # Copy the source directory and exec from it.
    env = os.environ.copy()
    if 'AQDCONF' in env:
        env.pop('AQDCONF')
    srcdir = config.get('unittest', 'srcdir')
    mirrordir = config.get('unittest', 'mirrordir')
    if not os.path.exists(mirrordir):
        os.makedirs(mirrordir)
    p = Popen(['rsync', '-avP', '--delete', srcdir + '/', mirrordir],
              stdout=1, stderr=2)
    p.communicate()
    if p.returncode != 0:
        print >>sys.stderr, "Rsync failed!"
        sys.exit(1)
    args = [sys.executable, os.path.join(mirrordir, 'tests', 'runtests.py')]
    for o, a in opts:
        if o in ('-m', '--mirror'):
            continue
        args.append(o)
        if a is not None:
            args.append(a)
    os.execve(sys.executable, args, env)

makefile = os.path.join(SRCDIR, "Makefile")
prod_python = None
with open(makefile) as f:
    prod_python_re = re.compile(r'^PYTHON_SERVER_PROD\s*=\s*(.*?)\s*$')
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

# Execute this every run... the man page says that it should do the right
# thing in terms of not contacting the kdc very often.
p = Popen(config.get("kerberos", "krb5_keytab"), stdout=1, stderr=2)
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

# FIXME: Need to be careful about attempting to nuke templatesdir...
dirs = [config.get("database", "dbdir"), config.get("unittest", "scratchdir")]
for label in ["templatesdir", "domainsdir", "rundir", "logdir", "profilesdir",
              "depsdir", "hostsdir", "plenarydir", "builddir"]:
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

# Create DSDB coverage directory
dsdb_coverage_dir = os.path.join(config.get("unittest", "scratchdir"),
                                 "dsdb_coverage")
os.makedirs(dsdb_coverage_dir)
os.environ["AQTEST_DSDB_COVERAGE_DIR"] = dsdb_coverage_dir

suite = unittest.TestSuite()
# Relies on the oracle rebuild doing a nuke first.
suite.addTest(DatabaseTestSuite())
suite.addTest(BrokerTestSuite())
VerboseTextTestRunner(verbosity=verbosity).run(suite)
