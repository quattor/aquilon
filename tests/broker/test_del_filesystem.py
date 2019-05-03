#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008-2010,2012-2013,2015-2016,2019  Contributor
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
"""Module for testing the del filesystem command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelFilesystem(TestBrokerCommand):

    def test_del_filesystem(self):
        command = ["del_filesystem", "--filesystem=fs2",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

        command = ["del_filesystem", "--filesystem=iscsi0",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

        command = ["del_filesystem", "--filesystem=fsshared",
                   "--cluster=utvcs1"]
        self.successtest(command)

        # fs1 is not deleted here, it will be removed when the host is deleted.

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelFilesystem)
    unittest.TextTestRunner(verbosity=2).run(suite)
