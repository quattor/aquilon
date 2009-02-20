#!/ms/dist/python/PROJ/core/2.5.4-0/bin/python
"""Test module for rebuilding the database."""

import os
import __init__

import aquilon.aqdb.depends
import nose
import unittest

from subprocess import Popen, PIPE

from aquilon.config import Config

class TestRebuild(unittest.TestCase):

    def testrebuild(self):
        env = {}
        for (key, value) in os.environ.items():
            env[key] = value
        env["AQDCONF"] = Config().baseconfig

        cmd = ['./build_db.py', '--delete', '--populate']

        _DIR = os.path.dirname(os.path.realpath(__file__))
        p = Popen(cmd, stdout=1, stderr=2, env=env, cwd=_DIR)
        (out, err) = p.communicate()

        self.assertEqual(p.returncode, 0, "Database rebuild failed:\n%s" % err)


if __name__=='__main__':
    nose.runmodule()

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
