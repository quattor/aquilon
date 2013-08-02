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
"""Module for testing the add bunker command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestAddBunker(TestBrokerCommand):

    def testaddutbunker1(self):
        command = ['add_bunker', '--bunker=bucket1.ut', '--building=ut',
                   '--fullname=UT b1']
        self.noouttest(command)

    def testverifyaddutbunker1(self):
        command = "show bunker --bunker bucket1.ut"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Bunker: bucket1.ut", command)
        self.matchoutput(out, "Fullname: UT b1", command)

    def testaddutbunker2(self):
        command = ['add_bunker', '--bunker=bucket2.ut', '--room=utroom2']
        self.noouttest(command)

    def testaddnyb10(self):
        self.noouttest(["add_bunker", "--bunker", "nyb10.np",
                        "--building", "np"])

    def testverifyutbunker2(self):
        command = "show bunker --bunker bucket2.ut"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Bunker: bucket2.ut", command)
        self.matchoutput(out, "Fullname: bucket2.ut", command)

    def testverifyshowcsv(self):
        command = "show bunker --all --format=csv"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "bunker,bucket1.ut,building,ut", command)
        self.matchoutput(out, "bunker,bucket2.ut,room,utroom2", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddBunker)
    unittest.TextTestRunner(verbosity=2).run(suite)
