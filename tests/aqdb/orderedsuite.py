#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2013  Contributor
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
"""Test module for rebuilding the database."""
import os

from utils import load_classpath
load_classpath()

import nose
import unittest

from subprocess import Popen
from aquilon.config import Config

class TestRebuild(unittest.TestCase):
    def testrebuild(self):
        env = {}
        for (key, value) in os.environ.items():
            env[key] = value
        env["AQDCONF"] = Config().baseconfig

        cmd = ['./build_db.py', '--delete', '--populate', 'data/unittest.dump']

        _DIR = os.path.dirname(os.path.realpath(__file__))
        p = Popen(cmd, stdout=1, stderr=2, env=env, cwd=_DIR)
        (out, err) = p.communicate()

        self.assertEqual(p.returncode, 0,
                         "Database rebuild failed with returncode %s:\n"
                         "STDOUT:\n%s\nSTDERR:\n%s\n" %
                         (p.returncode, out, err))

    def runTest(self):
        self.testrebuild()

class DatabaseTestSuite(unittest.TestSuite):
    def __init__(self, *args, **kwargs):
        unittest.TestSuite.__init__(self, *args, **kwargs)
        self.addTest(unittest.TestLoader().loadTestsFromTestCase(TestRebuild))


if __name__ == '__main__':
    nose.runmodule()
