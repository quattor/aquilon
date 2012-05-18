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
"""Module for testing the update building command."""


import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUpdateBuilding(TestBrokerCommand):

    def test_102_updateaddress(self):
        self.dsdb_expect("update_building_aq -building_name tu "
                         "-building_addr 24 Cherry Lane")
        command = ["update", "building", "--building", "tu",
                   "--address", "24 Cherry Lane"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_103_verifyupdateaddress(self):
        command = "show building --building tu"
        out, err = self.successtest(command.split(" "))
        self.matchoutput(out, "Building: tu", command)
        self.matchoutput(out, "Address: 24 Cherry Lane", command)

    def test_104_updatecitybad(self):
        command = ["update", "building", "--building", "tu",
                   "--address", "20 Penny Lane", "--city", "ln"]
        err = self.badrequesttest(command)
        self.matchoutput(err,
                         "Bad Request: Cannot change hubs. City ln is in "
                         "Hub ln while Building tu is in Hub ny.",
                         command)

    def test_106_updatecity(self):
        self.dsdb_expect("update_building_aq -building_name tu "
                         "-building_addr 20 Penny Lane")
        self.dsdb_expect("delete_campus_building_aq -campus_name ny "
                         "-building_name tu")
        self.dsdb_expect("add_campus_building_aq -campus_name ta "
                         "-building_name tu")

        command = ["update", "building", "--building", "tu",
                   "--address", "20 Penny Lane", "--city", "e5"]
        err = self.statustest(command)
        self.matchoutput(err, "There are 1 service(s) mapped to the "
                         "old location of the (city ny), "
                         "please review and manually update mappings for "
                         "the new location as needed.", command)
        self.dsdb_verify()

    def test_107_verifyupdatecity(self):
        command = "show building --building tu"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Building: tu", command)
        self.matchoutput(out, "Address: 20 Penny Lane", command)
        self.matchoutput(out, "City e5", command)

    def test_110_update_ut_dnsdomain(self):
        command = ["update", "building", "--building", "ut",
                   "--default_dns_domain", "aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_115_verify_ut_dnsdomain(self):
        command = ["show", "building", "--building", "ut"]
        out = self.commandtest(command)
        self.matchoutput(out, "Default DNS Domain: aqd-unittest.ms.com",
                         command)

    def test_110_update_tu_dnsdomain(self):
        command = ["update", "building", "--building", "tu",
                   "--default_dns_domain", "aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_115_verify_tu_dnsdomain(self):
        command = ["show", "building", "--building", "tu"]
        out = self.commandtest(command)
        self.matchoutput(out, "Default DNS Domain: aqd-unittest.ms.com",
                         command)

    def test_120_update_tu_nodnsdomain(self):
        command = ["update", "building", "--building", "tu",
                   "--default_dns_domain", ""]
        self.noouttest(command)

    def test_125_verify_tu_dnsdomain_gone(self):
        command = ["show", "building", "--building", "tu"]
        out = self.commandtest(command)
        self.matchclean(out, "Default DNS Domain", command)
        self.matchclean(out, "aqd-unittest.ms.com", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateBuilding)
    unittest.TextTestRunner(verbosity=2).run(suite)
