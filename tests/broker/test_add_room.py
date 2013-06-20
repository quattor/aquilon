#!/usr/bin/env python2.6
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
"""Module for testing the add room command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddRoom(TestBrokerCommand):

    def testaddutroom1(self):
        command = ['add_room', '--room=utroom1', '--building=ut',
                   '--fullname=UT pod1']
        self.noouttest(command)

    def testverifyaddutroom1(self):
        command = "show room --room utroom1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Room: utroom1", command)
        self.matchoutput(out, "Fullname: UT pod1", command)

    def testaddutroom2(self):
        command = ['add_room', '--room=utroom2', '--building=ut']
        self.noouttest(command)

    def testverifyutroom2(self):
        command = "show room --room utroom2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Room: utroom2", command)
        self.matchoutput(out, "Fullname: utroom2", command)

    def testverifyshowcsv(self):
        command = "show room --all --format=csv"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "room,utroom1,building,ut", command)
        self.matchoutput(out, "room,utroom2,building,ut", command)

    def testaddnplab1(self):
        self.noouttest(["add_room", "--room", "np-lab1", "--building", "np",
                        "--fullname", "NP lab1"])


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddRoom)
    unittest.TextTestRunner(verbosity=2).run(suite)
