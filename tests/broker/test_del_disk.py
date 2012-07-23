#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013  Contributor
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
"""Module for testing the del disk command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelDisk(TestBrokerCommand):

    def testdelut3c1n3sda(self):
        self.noouttest(["del", "disk", "--machine", "ut3c1n3",
            "--controller", "scsi", "--size", "68"])

    def testdelut3c1n3sdb(self):
        self.noouttest(["del", "disk", "--machine", "ut3c1n3",
            "--disk", "c0d0"])

    def testverifydelut3c1n3sda(self):
        command = "show machine --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Disk: sda 68 GB scsi", command)

    def testverifydelut3c1n3sdb(self):
        command = "show machine --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Disk: c0d0", command)

    # This should now list the 34 GB disk that was added previously...
    def testverifycatut3c1n3disk(self):
        command = "cat --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "harddisks", command)

    def testfaildelunknowntype(self):
        command = ["del", "disk", "--machine", "ut3c1n3",
                   "--type", "type-does-not-exist"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "type-does-not-exist is not a valid controller type",
                         command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelDisk)
    unittest.TextTestRunner(verbosity=2).run(suite)
