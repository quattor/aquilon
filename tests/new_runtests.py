#!/usr/bin/env python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010 Contributor
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

import re
import os
import sys
import getopt
import shutil

from subprocess import Popen

BINDIR = os.path.dirname(os.path.realpath(__file__))
SRCDIR = os.path.join(BINDIR, "..")
sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

import aquilon.aqdb.depends
import setuptools
import argparse
import nose

from aquilon.config import Config
from aquilon.utils import kill_from_pid_file, confirm
from verbose_text_test import VerboseTextTestRunner

from broker.short_suite import BrokerTestSuite
#from broker.orderedsuite import BrokerTestSuite
from aqdb.orderedsuite import DatabaseTestSuite


def parse_args(*args, **kw):
    p = argparse.ArgumentParser(
        description = 'Nose based test runner for aquilons regression tests',
        epilog = 'NOTE: $AQDCONF environment variable is not used by default.')

    p.add_argument('-v', '--verbose',
                   action = 'count',
                   dest = 'verbosity',
                   default = 1,
                   help = 'increase verbosity by adding more (-vv), etc.')

    p.add_argument('--config',
                   dest = 'configfile',
                   default = os.path.join(BINDIR, "unittest.conf"),
                   help = 'The configfile to be used.')

    #TODOs
    # -x/--stop, to pass through to nose, stop/start as fixtures as an option.
    # setup coverage to pass through to nose
    # -s/--nocapture to pass through to nose

    p.add_argument('--coverage',
                   action = 'store_true',
                   default = False,
                   dest = 'coverage',
                   help = 'enable code coverage reporting')

    return p.parse_args()
    #TODO: move validation code into this function


def main(*args, **kw):
    """ Run them tests! """
    try:
        opts = parse_args(*args, **kw)
    except Exception, e:
        print e
        sys.exit(-1)

    if not os.path.exists(opts.configfile):
        print >> sys.stderr, "configfile %s does not exist" % opts.configfile
        sys.exit(1)

    _prompt = """Will ignore AQDCONF variable value:
%s
and use
%s
instead.""" % (os.environ["AQDCONF"], opts.configfile)

    if os.environ.get("AQDCONF") and (os.path.realpath(opts.configfile)
            != os.path.realpath(os.environ["AQDCONF"])):
        if not confirm(prompt=_prompt, resp=False):
            sys.exit(0)

    config = Config(configfile=opts.configfile)
    if not config.has_section("unittest"):
        config.add_section("unittest")
    if not config.has_option("unittest", "srcdir"):
        config.set("unittest", "srcdir", SRCDIR)
    if opts.coverage:
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
        _prompt = "\nRunning with %s but prod is %s" % (sys.executable, prod_python)
        if not confirm(prompt=_prompt, resp=False):
            sys.exit(0)

    #TODO: replace with db_factory.is_prod_db
    production_database = "NYPO_AQUILON"
    if (config.get("database", "vendor") == "oracle" and
            config.get("database", "server") == production_database):
        print 'Can not run against prod database %s' % production_database
        sys.exit(-1)

    # Maybe just execute this every run...
    if not os.path.exists("/var/spool/keytabs/%s" % config.get("broker", "user")):
        p = Popen(("/ms/dist/kerberos/PROJ/krb5_keytab/prod/sbin/krb5_keytab"),
                stdout=1, stderr=2)
        rc = p.wait()

    pid_file = os.path.join(config.get('broker', 'rundir'), 'aqd.pid')
    kill_from_pid_file(pid_file)

    for label in ["quattordir", "kingdir", "swrepdir", ]:
        directory = config.get("broker", label)
        if os.path.exists(directory):
            continue
        try:
            os.makedirs(directory)
        except OSError, e:
            print >> sys.stderr, "Could not create %s: %s" % (directory, e)

    dirs = [config.get("database", "dbdir"), config.get("unittest", "scratchdir")]
    for label in ["templatesdir", "rundir", "logdir", "profilesdir",
                  "depsdir", "hostsdir", "plenarydir", "builddir"]:
        dirs.append(config.get("broker", label))

    #TODO: replace with call to confirm
    #if configfile != default_configfile:
    #    force_yes(
    #        "About to remove any of the following directories that exist:\n%s\n"
    #        % "\n".join(dirs))

    for directory in dirs:
        if os.path.exists(directory):
            #maybe TODO: only print if verbose/debug
            print "Removing %s" % directory
            shutil.rmtree(directory, ignore_errors=True)

        try:
            os.makedirs(directory)
        except OSError, e:
            print >> sys.stderr, "Could not create %s: %s" % (directory, e)


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

    suite = nose.suite.LazySuite()

    # Relies on the oracle rebuild doing a nuke first.
    suite.addTest(DatabaseTestSuite())
    suite.addTest(BrokerTestSuite())

    #it takes a bit of time to start things up. This message keeps impatient people
    #aware of what's happening instead of thinking non essentials are wasting time
    print "starting up the test runner"

    #TODO: construct an args list for nose.run to add the stop, the debug, etc.
    nose.run(suite=suite,
        testRunner=VerboseTextTestRunner(verbosity=opts.verbosity))


if __name__ == '__main__':
    main(sys.argv)

#
# TODO: add --useenv option to take config file from $AQDCONF
#
#class SetConfig(argparse.Action):
#    """ custom action to set the option from users environment """
#    def __call__(self, parser, namespace, values, option_string=None):
#        print '%r %r %r' % (namespace, values, option_string)
#        setattr(namespace, self.dest, os.environ["AQDCONF"])
