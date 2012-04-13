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
"""Module for testing the del building command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelBuilding(TestBrokerCommand):

    def testdelbu(self):
        self.dsdb_expect("delete_campus_building_aq -campus_name ny "
                         "-building_name bu")
        self.dsdb_expect("delete_building_aq -building bu")
        command = "del building --building bu"
        self.noouttest(command.split(" "))
        self.dsdb_verify()

    def testverifydelbu(self):
        command = "show building --building bu"
        self.notfoundtest(command.split(" "))

    def testdelex(self):
        self.dsdb_expect("delete_building_aq -building cards")
        command = "del building --building cards"
        self.noouttest(command.split(" "))
        self.dsdb_verify()

    def testdelbunotindsdb(self):
        ## add building

        test_building = "bz"
        self.dsdb_expect("add_building_aq -building_name bz -city ex "
                         "-building_addr Nowhere")
        command = ["add", "building", "--building", test_building, "--city", "ex",
                   "--address", "Nowhere"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "WARNING: There's no campus for city ex of "
                         "building bz. dsdb add_campus_building will not be "
                         "executed.", command)
        self.dsdb_verify()


        dsdb_command = "delete_building_aq -building %s" % test_building
        errstr = "bldg %s doesn't exists" % test_building
        self.dsdb_expect(dsdb_command, True, errstr)
        command = "del building --building %s" % test_building
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        self.dsdb_verify()

    def testdelnettest02(self):
        self.dsdb_expect("delete_campus_building_aq -campus_name ny "
                         "-building_name nettest")
        self.dsdb_expect("delete_building_aq -building nettest")
        command = "del building --building nettest"
        self.noouttest(command.split(" "))
        self.dsdb_verify()

    def testdelnettest01(self):
        test_bu = "nettest"

        # add network to building
        self.noouttest(["add_network", "--ip", "192.176.6.0",
                        "--network", "test_warn_network",
                        "--netmask", "255.255.255.0",
                        "--building", test_bu,
                        "--type", "unknown",
                        "--comments", "Made-up network"])

        # try delete building
        command = "del building --building %s" % test_bu
        err = self.badrequesttest(command.split(" "))
        self.matchoutput(err,
                         "Bad Request: Could not delete building %s, "
                         "networks were found using this location." % test_bu,
                         command)
        self.dsdb_verify(empty=True)

        # delete network
        self.noouttest(["del_network", "--ip", "192.176.6.0"])


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelBuilding)
    unittest.TextTestRunner(verbosity=2).run(suite)
