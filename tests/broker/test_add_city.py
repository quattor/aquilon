#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010,2011  Contributor
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
"""Module for testing the add city command."""

import os
import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddCity(TestBrokerCommand):

    def testaddexample(self):
        self.dsdb_expect("add_city_aq -city_symbol ex " +
                         "-country_symbol us -city_name Exampleton")
        command = ["add", "city", "--city", "ex", "--country", "us",
                   "--fullname", "Exampleton", "--timezone",
                   "US/Eastern", "--comments", "Example city comment"]
        self.noouttest(command)
        self.dsdb_verify()

    def testaddupdateexample(self):
        command = ["update", "city", "--city", "ex",
                   "--timezone", "EDT",
                   "--comments", "Exampleton city comment"]
        self.ignoreoutputtest(command)
        # For a difference, let's use raw this time
        command = "show city --city ex"
        (out, err) = self.successtest(command.split(" "))
        self.matchoutput(out, "Timezone: EDT", command)

    def testaddexamplefail(self):
        self.dsdb_expect("add_city_aq -city_symbol e2 " +
                         "-country_symbol us -city_name Exampleville",
                         fail=True)
        command = ["add", "city", "--city", "e2", "--country", "us",
                   "--fullname", "Exampleville", "--timezone",
                   "US/Eastern"]
        self.badrequesttest(command)
        self.dsdb_verify()

    def testaddexampledefault(self):
        self.dsdb_expect("add_city_aq -city_symbol e3 " +
                         "-country_symbol us -city_name Exampleby")
        command = ["add", "city", "--city", "e3", "--country", "us",
                   "--fullname", "Exampleby", "--timezone", "UTC"]
        self.noouttest(command)
        self.dsdb_verify()

    def testplenary(self):
        command = ["cat", "--city", "ex"]
        out = self.commandtest(command)
        self.matchoutput(out, 'variable TIMEZONE = "EDT";', command)

    def testplenarydefault(self):
        command = ["cat", "--city", "e3"]
        out = self.commandtest(command)
        self.matchoutput(out, 'variable TIMEZONE = "UTC";', command)

    def testverifyex(self):
        command = "show city --city ex"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "City: ex", command)
        self.matchoutput(out, "Comments: Exampleton city comment", command)

    def testverifyexproto(self):
        command = "show city --city ex --format proto"
        out = self.commandtest(command.split(" "))
        locs = self.parse_location_msg(out, 1)
        self.matchoutput(locs.locations[0].name, "ex", command)
        self.matchoutput(locs.locations[0].location_type, "city", command)
        self.matchoutput(locs.locations[0].fullname, "Exampleton", command)
        self.matchoutput(locs.locations[0].timezone, "EDT", command)

    def testverifycityall(self):
        command = ["show", "city", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "City: ex", command)

    def testverifyshowcsv(self):
        command = "show city --city ex --format=csv"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "city,ex,country,us,,,EDT,Exampleton",
                         command)

    def testupdatecity00(self):
        ## add city
        self.dsdb_expect("add_city_aq -city_symbol e4 " +
                         "-country_symbol us -city_name Exampleby")
        command = ["add", "city", "--city", "e4", "--country", "us",
                   "--fullname", "Exampleby", "--timezone", "US/Eastern"]
        self.noouttest(command)
        self.dsdb_verify()

        ## add building
        self.dsdb_expect("add_building_aq -building_name bx -city e4 "
                         "-building_addr Nowhere")
        command = ["add", "building", "--building", "bx", "--city", "e4",
                   "--address", "Nowhere"]
        out, err = self.successtest(command)
        self.matchoutput(err, "WARNING: There's no campus for city e4 of "
                         "building bx. dsdb add_campus_building "
                         "will not be executed.", command)
        self.dsdb_verify()

        ## add campus
        command = ["add", "location", "--type", "campus", "--name", "na",
                   "--parenttype", "country", "--parentname", "us",
                   "--fullname", "test campus"]
        self.noouttest(command)

        # update city
        self.dsdb_expect("update_city_aq -city e4 -campus na")
        command = ["update", "city", "--city", "e4", "--campus", "na"]
        self.ignoreoutputtest(command)
        self.dsdb_verify()

        command = "show city --city e4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Location Parents: [Organization ms, Hub ny, "
                         "Continent na, Country us, Campus na]", command)

        command = "show building --building bx"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Location Parents: [Organization ms, Hub ny, "
                    "Continent na, Country us, Campus na, City e4]", command)

    def testaddcitycampus(self):
        ## add city
        self.dsdb_expect("add_city_aq -city_symbol e5 " +
                         "-country_symbol us -city_name Examplefive")
        command = ["add", "city", "--city", "e5", "--campus", "ta",
                   "--fullname", "Examplefive", "--timezone",   "US/Eastern"]
        self.noouttest(command)
        self.dsdb_verify()

    def testupdatecity10(self):
        ## update city bad campus
        command = ["update", "city", "--city", "e4", "--campus", "xx"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Campus xx not found", command)

        command = "show city --city e4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Location Parents: [Organization ms, Hub ny, "
                         "Continent na, Country us, Campus na]", command)

    def testupdatecity20(self):
        ## update city dsdb error
        self.dsdb_expect("update_city_aq -city e4 -campus ta", fail=True)
        command = ["update", "city", "--city", "e4", "--campus", "ta"]
        out = self.badrequesttest(command)
        self.dsdb_verify()

        command = "show city --city e4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Location Parents: [Organization ms, Hub ny, "
                         "Continent na, Country us, Campus na]", command)

    def testupdatecity30(self):

        ## add city
        self.dsdb_expect("add_city_aq -city_symbol e6 " +
                         "-country_symbol gb -city_name ExampleSix")

        command = ["add", "city", "--city", "e6", "--country", "gb",
                   "--fullname", "ExampleSix", "--timezone",   "Europe/London"]
        self.noouttest(command)

        ## update city bad campus
        command = ["update", "city", "--city", "e6", "--campus", "na"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Cannot change campus.  Campus na is in hub ny, while city e6 is in hub ln", command)

    def testupdatedefaultdns(self):
        command = ["update", "city", "--city", "ny",
                   "--default_dns_domain", "one-nyp.ms.com"]
        self.successtest(command)

    def testverifydefaultdns(self):
        command = ["show", "city", "--city", "ny"]
        out = self.commandtest(command)
        self.matchoutput(out, "Default DNS Domain: one-nyp.ms.com", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddCity)
    unittest.TextTestRunner(verbosity=2).run(suite)
