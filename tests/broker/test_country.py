#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011  Contributor
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
"""Module for testing the add/del/show country command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestCountry(TestBrokerCommand):

    def testadd(self):

        command = ["add", "country", "--country", "ct", "--fullname",
                   "country example", "--continent", "na",
                   "--comments", "test country"]
        self.noouttest(command)


    def testaddshow(self):
        command = "show country --country ct"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Country: ct", command)
        self.matchoutput(out, "  Fullname: country example", command)
        self.matchoutput(out, "  Comments: test country", command)
        self.matchoutput(out,
                         "  Location Parents: [Organization ms, Hub ny, "
                         "Continent na]",
                         command)

        command = "show country --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Country: ct", command)

    def testverifydel(self):
        command = "show country --country ct"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Country ct not found.", command)

        command = "show country --all"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Country: ct", command)


    def testdel(self):
        test_country = "ct"

        # add network to hub
        self.noouttest(["add_network", "--ip", "192.176.6.0",
                        "--network", "test_warn_network",
                        "--netmask", "255.255.255.0",
                        "--country", test_country,
                        "--type", "unknown",
                        "--comments", "Made-up network"])


        # try delete country
        command = "del country --country %s" % test_country
        err = self.badrequesttest(command.split(" "))
        self.matchoutput(err,
                         "Bad Request: Could not delete country %s, networks "
                         "were found using this location." % test_country,
                         command)

        # delete network
        self.noouttest(["del_network", "--ip", "192.176.6.0"])

    def testdel01(self):
        command = "del country --country ct"
        self.noouttest(command.split(" "))

        ## delete country again
        command = "del country --country ct"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Country ct not found.", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCountry)
    unittest.TextTestRunner(verbosity=2).run(suite)

