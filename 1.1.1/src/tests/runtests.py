#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This script is part of Aquilon
"""This sets up and runs the broker unit tests."""

import sys
import os
BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
SRCDIR = os.path.join(BINDIR, "..")
sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

import unittest
from subprocess import Popen

from aquilon.config import Config

from broker.orderedsuite import BrokerTestSuite
from aqdb.orderedsuite import DatabaseTestSuite

configfile = os.path.join(BINDIR, "unittest.conf")
# FIXME: Allow AQDCONF environment var to override?  Allow it to be
# passed in?  Maybe make the rm statements below opt-in if that's the case.
config = Config(configfile=configfile)
if not config.has_section("unittest"):
    config.add_section("unittest")
if not config.has_option("unittest", "srcdir"):
    config.set("unittest", "srcdir", SRCDIR)

if os.environ.get("USER") != config.get("broker", "user"):
    print >>sys.stderr, "Expected to be running as %s, instead running as %s.  Aborting" % (
            config.get("broker", "user"), os.environ.get("USER"))
    sys.exit(os.EX_CONFIG)

# Maybe just execute this every run...
if not os.path.exists("/var/spool/keytabs/%s" % config.get("broker", "user")):
    p = Popen(("/ms/dist/kerberos/PROJ/krb5_keytab/prod/sbin/krb5_keytab"),
            stdout=1, stderr=2)
    rc = p.wait()

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

p = Popen(("rsync", "-avP", "-e", "ssh", "--delete",
    "quattorsrv:/var/quattor/swrep/repository",
    config.get("broker", "swrepdir")),
    stdout=1, stderr=2)
rc = p.wait()
# FIXME: check rc

suite = unittest.TestSuite()
suite.addTest(DatabaseTestSuite())
suite.addTest(BrokerTestSuite())
unittest.TextTestRunner(verbosity=2).run(suite)

