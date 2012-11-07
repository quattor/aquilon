#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Module for testing the add rack command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddRack(TestBrokerCommand):

    def testaddut3(self):
        command = "add rack --rackid 3 --room utroom1 --row a --column 3"
        self.noouttest(command.split(" "))

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
