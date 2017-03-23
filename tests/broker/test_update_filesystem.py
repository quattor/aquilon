#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2016,2017  Contributor
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
"""Module for testing the update_filesystem command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand

class TestUpdateFilesystem(TestBrokerCommand):
    def test_00_update_basic_filesystem(self):
        command = ["update_filesystem", "--filesystem=fs1", "--type=ext3",
                   "--mountpoint=/mnt1", "--blockdevice=/dev/vx/dsk/dg.0/gnr.0",
                   "--dumpfreq=1", "--fsckpass=2", "--options=rw",
                   "--comments=Some updated filesystem comments",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

        command = ["show_filesystem", "--filesystem=fs1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Filesystem: fs1", command)
        self.matchoutput(out, "Bound to: Host server1.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Block Device: /dev/vx/dsk/dg.0/gnr.0", command)
        self.matchoutput(out, "Mount at boot: True", command)
        self.matchoutput(out, "Mountopts: rw", command)
        self.matchoutput(out, "Mountpoint: /mnt1", command)
        self.matchoutput(out, "Dump Freq: 1", command)
        self.matchoutput(out, "Fsck Pass: 2", command)
        self.matchoutput(out, "Comments: Some updated filesystem comments", command)

    def test_01_bad_fsckpass(self):
        command = ["update_filesystem", "--filesystem=fs1",
                   "--hostname=server1.aqd-unittest.ms.com", "--fsckpass=banana"]
        out = self.badoptiontest(command)

    def test_01_bad_hostname(self):
        command = ["update_filesystem", "--filesystem=fs1",
                   "--hostname=badhostname.aqd-unittest.ms.com",
                   "--comments=Some more updated filesystem comments"]
        out = self.notfoundtest(command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateFilesystem)
    unittest.TextTestRunner(verbosity=2).run(suite)
