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
"""Module for testing errors in the documentation."""

import os
import unittest
from subprocess import Popen, PIPE

if __name__ == '__main__':
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDocumentation(TestBrokerCommand):
    def test_100_run_make_check(self):
        srcdir = self.config.get("broker", "srcdir")
        docdir = os.path.join(srcdir, "doc")
        p = Popen(["make", "check"], stdout=PIPE, stderr=PIPE, cwd=docdir)
        out, err = p.communicate()
        self.assertEqual(p.returncode, 0,
                         "Running 'make check' on the documentation failed: "
                         "STDOUT:\n@@@\n'%s'\n@@@\nSTDERR:\n@@@\n'%s'\n@@@\n"
                         % (out, err))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDocumentation)
    unittest.TextTestRunner(verbosity=2).run(suite)
