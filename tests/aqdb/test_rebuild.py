#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
"""Test module for rebuilding the database."""

import os
import sys
import unittest
from subprocess import Popen, PIPE

_DIR = os.path.dirname(os.path.realpath(__file__))
_LIBDIR = os.path.join(_DIR, "..", "..", "lib", "python2.5")

if _LIBDIR not in sys.path:
    sys.path.insert(0, _LIBDIR)

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
        vendor = config.get("database", "vendor")
        if vendor == 'sqlite':
            dbfile = config.get("database", "dbfile")
            if os.path.exists(dbfile):
                os.unlink(dbfile)
        elif vendor == 'oracle':
            # Maybe drop_all_tables_and_sequences()...
            pass
        # Hack for ipshell...
        if config.get("broker", "user") == 'cdb':
            env["HOME"] = config.get("broker", "basedir")

        cmd = ['./build_db.py', '--populate']
        print os.getcwd()

        p = Popen(cmd, stdout=1, stderr=2, env=env, cwd=_DIR)
        (out, err) = p.communicate()

        self.assertEqual(p.returncode, 0, "Database rebuild failed:\n%s" % err)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRebuild)
    unittest.TextTestRunner(verbosity=2).run(suite)

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
