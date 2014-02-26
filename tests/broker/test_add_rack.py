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
"""Module for testing the add rack command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestAddRack(TestBrokerCommand):

    def testaddut3(self):
        command = "add rack --rackid 3 --room utroom1 --row a --column 3"
        self.noouttest(command.split(" "))

    def testaddut3again(self):
        command = "add rack --rackid 3 --room utroom1 --row a --column 3"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Rack ut3 already exists.", command)

    def testverifyaddut3(self):
        command = "show rack --rack ut3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Rack: ut3", command)
        self.matchoutput(out, "Row: a", command)
        self.matchoutput(out, "Column: 3", command)

    def testaddcards1(self):
        command = "add rack --rackid 1 --building cards --row a --column 1"
        self.noouttest(command.split(" "))

    def testverifyaddcards1(self):
        command = "show rack --rack cards1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Rack: cards1", command)
        self.matchoutput(out, "Row: a", command)
        self.matchoutput(out, "Column: 1", command)

    def testaddnp3(self):
        command = "add rack --rackid 3 --building np --row a --column 3"
        self.noouttest(command.split(" "))

    def testaddut4(self):
        command = "add rack --rackid 4 --room utroom1 --row a --column 4"
        self.noouttest(command.split(" "))

    def testaddut8(self):
        command = "add rack --rackid 8 --building ut --row g --column 2"
        self.noouttest(command.split(" "))

    def testaddut9(self):
        command = "add rack --rackid 9 --bunker bucket2.ut --row g --column 3"
        self.noouttest(command.split(" "))

    def testverifyut9(self):
        command = "show rack --rack ut9"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Location Parents: [Organization ms, Hub ny, "
                         "Continent na, Country us, Campus ny, City ny, "
                         "Building ut, Room utroom2, Bunker bucket2.ut]",
                         command)

    def testaddut10(self):
        command = "add rack --rackid 10 --building ut --row g --column 4"
        self.noouttest(command.split(" "))

    def testaddut11(self):
        command = "add rack --rackid 11 --building ut --row k --column 1"
        self.noouttest(command.split(" "))

    def testaddut12(self):
        command = "add rack --rackid 12 --building ut --row k --column 2"
        self.noouttest(command.split(" "))

    def testaddnp7(self):
        command = "add rack --rackid 7 --building np --row g --column 1"
        self.noouttest(command.split(" "))

    def testaddnp997(self):
        command = "add rack --rackid np997 --building np --row ZZ --column 99"
        self.noouttest(command.split(" "))

    def testaddnp998(self):
        command = "add rack --rackid np998 --building np --row yy --column 88"
        self.noouttest(command.split(" "))

    def testaddnp999(self):
        command = "add rack --rackid np999 --building np --row zz --column 11"
        self.noouttest(command.split(" "))

    def testaddut13(self):
        command = "add rack --rackid 13 --building ut --row k --column 3"
        self.noouttest(command.split(" "))

    def testaddnp13(self):
        command = "add rack --rackid 13 --building np --row k --column 3"
        self.noouttest(command.split(" "))

    def testverifyaddnp997(self):
        command = "show rack --rack np997"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Rack: np997", command)
        self.matchoutput(out, "Row: zz", command)
        self.matchoutput(out, "Column: 99", command)

    def testaddnewalphanumericrack(self):
        command = "add rack --rackid np909 --building np --row 99 --column zz"
        self.noouttest(command.split(" "))

    def testverifynp909(self):
        command = "show rack --rack np909"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Rack: np909", command)
        self.matchoutput(out, "Row: 99", command)
        self.matchoutput(out, "Column: zz", command)

    def testverifyshowallcsv(self):
        command = "show rack --all --format=csv"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "rack,ut3,room,utroom1,a,3", command)
        self.matchoutput(out, "rack,np997,building,np,zz,99", command)
        self.matchoutput(out, "rack,np909,building,np,99,zz", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddRack)
    unittest.TextTestRunner(verbosity=2).run(suite)
