#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014,2015  Contributor
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
"""Module for testing the vulcan2 related commands."""

from datetime import datetime
import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand
from notificationtest import VerifyNotificationsMixin


class TestVulcanLocalDisk(VerifyNotificationsMixin, TestBrokerCommand):

    def test_070_try_delete_vmhost(self):
        command = ["del_host", "--hostname", "evh82.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Host evh82.aqd-unittest.ms.com still has virtual "
                         "machines: evm50, evm51, evm52.",
                         command)

    def test_122_addvmfswohost(self):
        # Try to bind to fs1 of another host.
        command = ["add", "disk", "--machine", "evm50",
                   "--disk", "sdb", "--controller", "scsi",
                   "--filesystem", "utfs1n", "--address", "0:1",
                   "--size", "34"]

        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Host evh82.aqd-unittest.ms.com does not have "
                         "filesystem utfs1n assigned to it.",
                         command)

    def test_156_del_used_filesystem(self):
        command = ["del_filesystem", "--filesystem", "utfs1",
                   "--hostname", "evh82.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Filesystem utfs1 has virtual disks attached, "
                         "so it cannot be deleted.", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestVulcanLocalDisk)
    unittest.TextTestRunner(verbosity=2).run(suite)
