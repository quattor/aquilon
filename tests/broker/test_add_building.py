#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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
        command = ["add", "building", "--building", "bu", "--city", "ny",
                   "--address", "12 Cherry Lane"]
        self.noouttest(command)
        self.dsdb_verify()

    def testverifyaddbu(self):
        command = "show building --building bu"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Building: bu", command)


    def testaddbucards(self):
        self.dsdb_expect("add_building_aq -building_name cards -city ex "
                         "-building_addr Nowhere")
        command = ["add", "building", "--building", "cards", "--city", "ex",
                   "--address", "Nowhere"]
        self.noouttest(command)
        self.dsdb_verify()

    def testverifyaddbucards(self):
        command = "show building --building cards"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Building: cards", command)

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


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddBuilding)
    unittest.TextTestRunner(verbosity=2).run(suite)
