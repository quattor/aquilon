#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This script is part of Aquilon
"""This sets up and runs the broker unit tests."""

import os
import sys
import getopt
import unittest
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
    opts, args = getopt.getopt(sys.argv[1:], "hdc:",
                               ["help", "debug", "config=", "coverage"])
except getopt.GetoptError, e:
    print >>sys.stderr, str(e)
    usage()
    sys.exit(2)

configfile = default_configfile
coverage = False
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

template_king_host = config.get("unittest", "template_king_host")
# The template-king also gets synced as part of the broker tests,
# but this makes it available for the initial database build.
p = Popen(("rsync", "-avP", "-e", "ssh", "--delete",
    "%s:/var/quattor/template-king" % template_king_host,
    # Minor hack... ignores config kingdir...
    config.get("broker", "quattordir")),
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
    def addError(self, test, err):
        unittest._TextTestResult.addError(self, test, err)

    def addFailure(self, test, err):
        unittest._TextTestResult.addFailure(self, test, err)
        self.stream.writeln("%s" % self.failures[-1][1])


class VerboseTextTestRunner(unittest.TextTestRunner):
    def _makeResult(self):
        return VerboseTextTestResult(self.stream, self.descriptions,
                                     self.verbosity)


suite = unittest.TestSuite()
# Relies on the oracle rebuild doing a nuke first.
suite.addTest(DatabaseTestSuite())
suite.addTest(BrokerTestSuite())
VerboseTextTestRunner(verbosity=2).run(suite)
