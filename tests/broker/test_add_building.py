#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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
"""Module for testing the add building command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddBuilding(TestBrokerCommand):

    def testaddbu(self):
        self.dsdb_expect("add_building_aq -building_name bu -city ny "
                         "-building_addr 12 Cherry Lane")
        self.dsdb_expect("add_campus_building_aq -campus_name ny "
                         "-building_name bu")
        command = ["add", "building", "--building", "bu", "--city", "ny",
                   "--address", "12 Cherry Lane"]
        self.noouttest(command)
        self.dsdb_verify()

    def testverifyaddbu(self):
        command = "show building --building bu"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Building: bu", command)
        self.matchoutput(out, "Address: 12 Cherry Lane", command)

    def testaddbucards(self):
        self.dsdb_expect("add_building_aq -building_name cards -city ex "
                         "-building_addr Nowhere")
        # No campus for city ex
#        self.dsdb_expect("add_campus_building_aq -campus_name ny "
#                         "-building_name bu")
        command = ["add", "building", "--building", "cards", "--city", "ex",
                   "--address", "Nowhere"]
        err = self.statustest(command)
        self.matchoutput(err, "WARNING: There's no campus for city %s of "
                               "building %s. dsdb add_campus_building will "
                               "not be executed." % ("ex", "cards"), command)
        self.dsdb_verify()

    def testverifyaddbucards(self):
        command = "show building --building cards"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Building: cards", command)
        self.matchoutput(out, "Address: Nowhere", command)

    def testverifyaddbuproto(self):
        command = "show building --building bu --format proto"
        out = self.commandtest(command.split(" "))
        locs = self.parse_location_msg(out, 1)
        self.matchoutput(locs.locations[0].name, "bu", command)
        self.matchoutput(locs.locations[0].location_type, "building", command)

    def testverifybuildingall(self):
        command = ["show", "building", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Building: ut", command)

    def testverifyshowcsv(self):
        command = "show building --building bu --format=csv"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "building,bu,city,ny", command)

    def testaddnettest(self):
        self.dsdb_expect("add_building_aq -building_name nettest -city ny "
                         "-building_addr Nowhere")
        self.dsdb_expect("add_campus_building_aq -campus_name ny "
                         "-building_name nettest")
        command = ["add", "building", "--building", "nettest", "--city", "ny",
                   "--address", "Nowhere"]
        self.noouttest(command)
        self.dsdb_verify()

    def testnonascii(self):
        command = ["add", "building", "--building", "nonascii", "--city", "ny",
                   "--address", "\xe1\xe9\xed\xf3\xfa"]
        self.dsdb_expect("add_campus_building_aq -campus_name ny "
                         "-building_name nonascii")
        out = self.badrequesttest(command)
        self.matchoutput(out, "Only ASCII characters are allowed for --address.",
                         command)

    def testnonasciiaudit(self):
        command = ["search", "audit", "--keyword", "nonascii"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r"400 aq add_building .*"
                          r"--address='<Non-ASCII value>'",
                          command)
        self.searchoutput(out, r"400 aq add_building .*--building='nonascii'",
                          command)

    def test_addtu(self):
        self.dsdb_expect("add_building_aq -building_name tu -city ny "
                         "-building_addr 14 Test Lane")
        self.dsdb_expect("add_campus_building_aq -campus_name ny "
                         "-building_name tu")
        command = ["add", "building", "--building", "tu", "--city", "ny",
                   "--address", "14 Test Lane"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_verifyaddtu(self):
        command = "show building --building tu"
        out, err = self.successtest(command.split(" "))
        self.matchoutput(out, "Building: tu", command)
        self.matchoutput(out, "Address: 14 Test Lane", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddBuilding)
    unittest.TextTestRunner(verbosity=2).run(suite)
