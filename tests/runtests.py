#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""This sets up and runs the broker unit tests."""


import os
import re
import sys
from subprocess import Popen

import depends  # pylint: disable=W0611
import unittest2 as unittest

import argparse

BINDIR = os.path.dirname(os.path.realpath(__file__))
SRCDIR = os.path.join(BINDIR, "..")
sys.path.append(os.path.join(SRCDIR, "lib"))

from aquilon.config import Config
from aquilon.utils  import kill_from_pid_file
from verbose_text_test import VerboseTextTestRunner

from broker.orderedsuite import BrokerTestSuite
from aqdb.orderedsuite import DatabaseTestSuite

default_configfile = os.path.join(BINDIR, "unittest.conf")

epilog = """
    Note that:
    %s
    will be used by default, and setting the AQDCONF environment variable
    will *not* work to pass in a config.

    The mirror option can be used to continue work in your local tree
    without breaking the in-progress tests.  It copies all the source
    code into the directory given in the mirrordir option of the unittest
    section of the config and then re-launches the tests from there.
    """ % default_configfile


def force_yes(msg):
    print >> sys.stderr, msg
    print >> sys.stderr, """
        Please confirm by typing yes (three letters) and pressing enter.
        """
    answer = sys.stdin.readline()
    if not answer.startswith("yes"):
        print >> sys.stderr, """Aborting."""
        sys.exit(1)

parser = argparse.ArgumentParser(description="Run the broker test suite.",
                                 epilog=epilog)
parser.add_argument('-v', '--verbose', action='count', dest='verbose',
                    default=1,
                    help='list each test name as it runs')
parser.add_argument('-q', '--quiet', dest='verbose', action='store_const',
                    const=0,
                    help='do not print the module names during tests')
parser.add_argument('-c', '--config', dest='config',
                    default=default_configfile,
                    help='supply an alternate config file')
parser.add_argument('--coverage', action='store_true',
                    help='generate code coverage metrics for the broker in '
                         'logs/coverage')
parser.add_argument('--profile', action='store_true',
                    help='generate profiling information for the broker in '
                         'logs/aqd.profile (currently broken)')
parser.add_argument('-m', '--mirror', action='store_true',
                    help='copy source to an alternate location and re-exec')

opts = parser.parse_args()

if not os.path.exists(opts.config):
    print >> sys.stderr, "configfile %s does not exist" % opts.config
    sys.exit(1)

if os.environ.get("AQDCONF") and (os.path.realpath(opts.config)
        != os.path.realpath(os.environ["AQDCONF"])):
    force_yes("""Will ignore AQDCONF variable value:
%s
and use
%s
instead.""" % (os.environ["AQDCONF"], opts.config))

config = Config(configfile=opts.config)
if not config.has_section("unittest"):
    config.add_section("unittest")
if not config.has_option("unittest", "srcdir"):
    config.set("unittest", "srcdir", SRCDIR)
if opts.coverage:
    config.set("unittest", "coverage", "True")
if opts.profile:
    config.set("unittest", "profile", "True")

hostname = config.get("unittest", "hostname")
if hostname.find(".") < 0:
    print >> sys.stderr, """
Some regression tests depend on the config value for hostname to be
fully qualified.  Please set the config value manually since the default
on this system (%s) is a short name.
""" % hostname
    sys.exit(1)

if opts.mirror:
    # Copy the source directory and exec from it.
    env = os.environ.copy()
    if 'AQDCONF' in env:
        env.pop('AQDCONF')
    srcdir = config.get('unittest', 'srcdir')
    mirrordir = config.get('unittest', 'mirrordir')
    if not os.path.exists(mirrordir):
        os.makedirs(mirrordir)
    p = Popen(['rsync', '-avP', '-e', 'ssh -q -o StrictHostKeyChecking=no " \
              + "-o UserKnownHostsFile=/dev/null -o BatchMode=yes',
              '--delete', srcdir + '/', mirrordir],
              stdout=1, stderr=2)
    p.communicate()
    if p.returncode != 0:
        print >> sys.stderr, "Rsync failed!"
        sys.exit(1)
    args = [sys.executable, os.path.join(mirrordir, 'tests', 'runtests.py')]
    args.extend(sys.argv[1:])
    if '--mirror' in args:
        args.remove('--mirror')
    if '-m' in args:
        args.remove('-m')
    os.execve(sys.executable, args, env)

makefile = os.path.join(SRCDIR, "Makefile")
prod_python = None
with open(makefile) as f:
    prod_python_re = re.compile(r'^PYTHON_SERVER_PROD\s*=\s*(\S+)(\s+|$)')
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

# Execute this every run... the man page says that it should do the right
# thing in terms of not contacting the kdc very often.
p = Popen(config.get("kerberos", "krb5_keytab"), stdout=1, stderr=2)
rc = p.wait()

pid_file = os.path.join(config.get('broker', 'rundir'), 'aqd.pid')
kill_from_pid_file(pid_file)

# FIXME: Need to be careful about attempting to nuke templatesdir...
dirs = [config.get("unittest", "scratchdir")]
if config.has_option("database", "dbfile"):
    dirs.append(os.path.dirname(config.get("database", "dbfile")))
for label in ["quattordir", "templatesdir", "domainsdir", "rundir", "logdir",
              "profilesdir", "plenarydir", "cfgdir", "kingdir", "swrepdir"]:
    dirs.append(config.get("broker", label))

existing_dirs = [d for d in dirs if os.path.exists(d)]

if existing_dirs:
    force_yes("About to remove the following directories:\n%s\n" %
              "\n\t".join(existing_dirs))

for dirname in existing_dirs:
    print "Removing %s" % dirname
    p = Popen(("/bin/rm", "-rf", dirname), stdout=1, stderr=2)
    rc = p.wait()
    # FIXME: check rc

for dirname in dirs:
    try:
        if not os.path.exists(dirname):
            os.makedirs(dirname)
    except OSError, e:
        print >> sys.stderr, "Could not create %s: %s" % (dirname, e)

# Set up DSDB coverage directory
dsdb_coverage_dir = os.path.join(config.get("unittest", "scratchdir"),
                                 "dsdb_coverage")
os.environ["AQTEST_DSDB_COVERAGE_DIR"] = dsdb_coverage_dir

suite = unittest.TestSuite()
# Relies on the oracle rebuild doing a nuke first.
suite.addTest(DatabaseTestSuite())
suite.addTest(BrokerTestSuite())
result = VerboseTextTestRunner(verbosity=opts.verbose).run(suite)
sys.exit(not result.wasSuccessful())
