#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Test module for rebuilding the database."""

import os
import sys
import unittest
from subprocess import Popen, PIPE

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from aquilon.config import Config


class TestRebuild(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testrebuild(self):
        config = Config()
        env = {}
        for (key, value) in os.environ.items():
            env[key] = value
        env["AQDCONF"] = config.baseconfig
        env["AQDBFILE"] = config.get("database", "dbfile")
        aqdbdir = os.path.join(config.get("broker", "srcdir"), "lib",
                "python2.5", "aquilon", "aqdb")
        p = Popen("./utils/REBUILD.sh", stdout=PIPE, stderr=PIPE,
                env=env, cwd=aqdbdir)
        (out, err) = p.communicate()
        self.assertEqual(p.returncode, 0, "Database rebuild failed:\n%s" % err)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRebuild)
    unittest.TextTestRunner(verbosity=2).run(suite)

