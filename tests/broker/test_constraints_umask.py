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
"""Module for testing constraints in commands involving the umask setting."""

import os
import stat

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestUmaskConstraints(TestBrokerCommand):

    # Check that all of the git commands have created files as readable
    # by all.
    def testgitfilepermission(self):
        self.assert_(os.stat(os.path.join(self.config.get("broker", "kingdir"),
                                          "refs", "heads", "utsandbox")
                            ).st_mode & stat.S_IROTH)

    # Check that directory created by the broker has the proper
    # permissions.  This gets created as part of test_make_aquilon.
    def testdirpermission(self):
        qdir = self.config.get('broker', 'quattordir')
        dirstat = os.stat(os.path.join(qdir, 'build', 'xml', 'unittest'))
        self.assert_(dirstat.st_mode & stat.S_IROTH)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUmaskConstraints)
    unittest.TextTestRunner(verbosity=2).run(suite)
