#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
import unittest
from subprocess import Popen

import depends  # pylint: disable=W0611

import argparse

BINDIR = os.path.dirname(os.path.realpath(__file__))
SRCDIR = os.path.join(BINDIR, "..")
sys.path.append(os.path.join(SRCDIR, "lib", "python2.6"))

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
parser.add_argument('-c', '--config', dest='config', default=default_configfile,
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
if (config.get("database", "dsn").startswith("oracle") and
        config.get("database", "server") == production_database):
    force_yes("About to run against the production database %s" %
            production_database)

# Execute this every run... the man page says that it should do the right
# thing in terms of not contacting the kdc very often.
p = Popen(config.get("kerberos", "krb5_keytab"), stdout=1, stderr=2)
rc = p.wait()

pid_file = os.path.join(config.get('broker', 'rundir'), 'aqd.pid')
kill_from_pid_file(pid_file)

# FIXME: Need to be careful about attempting to nuke templatesdir...
dirs = [config.get("database", "dbdir"), config.get("unittest", "scratchdir")]
for label in ["quattordir", "templatesdir", "domainsdir", "rundir", "logdir",
              "profilesdir", "plenarydir", "builddir", "kingdir", "swrepdir"]:
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

# Create DSDB coverage directory
dsdb_coverage_dir = os.path.join(config.get("unittest", "scratchdir"),
                                 "dsdb_coverage")
os.makedirs(dsdb_coverage_dir)
os.environ["AQTEST_DSDB_COVERAGE_DIR"] = dsdb_coverage_dir

suite = unittest.TestSuite()
# Relies on the oracle rebuild doing a nuke first.
suite.addTest(DatabaseTestSuite())
suite.addTest(BrokerTestSuite())
result = VerboseTextTestRunner(verbosity=opts.verbose).run(suite)
sys.exit(not result.wasSuccessful())
