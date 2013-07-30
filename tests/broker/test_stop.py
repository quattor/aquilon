#!/usr/bin/env python
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
"""Test module for stopping the broker."""

import os
import signal
from time import sleep

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from aquilon.config import Config


class TestBrokerStop(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def teststop(self):
        config = Config()
        pidfile = os.path.join(config.get("broker", "rundir"), "aqd.pid")
        self.assert_(os.path.exists(pidfile))
        f = file(pidfile)
        pid = f.readline()
        self.assertNotEqual(pid, "")
        f.close()
        pid = int(pid)
        os.kill(pid, signal.SIGTERM)

        # Wait for the broker to shut down. E.g. generating code coverage may
        # take some time.
        i = 0
        while i < 180:
            i += 1
            try:
                os.kill(pid, 0)
            except OSError:
                break
            sleep(1)

        # Verify that the broker is down
        self.failUnlessRaises(OSError, os.kill, pid, 0)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBrokerStop)
    unittest.TextTestRunner(verbosity=2).run(suite)
