#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
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
"""Module for testing the add organization command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestOrganization(TestBrokerCommand):

    def test_100_addexorg(self):
        command = ["add", "organization", "--organization", "example",
                   "--fullname", "Example, Inc"]
        self.noouttest(command)

        command = "show organization --organization example"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Organization: example", command)

    def test_100_addexorg2(self):
        command = ["add", "organization", "--organization", "example2"]
        self.noouttest(command)

        command = "show organization --organization example2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Organization: example2", command)

    def test_110_delexorg2(self):
        command = "del organization --organization example2"
        self.noouttest(command.split(" "))

    def test_120_delexorg2again(self):
        command = "del organization --organization example2"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Organization example2 not found.", command)

    def test_130_verifydelexorg2(self):
        command = "show organization --organization example2"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Organization example2 not found.", command)

    def test_140_delexorginuse(self):
        test_org = "example"

        # add network to org
        self.noouttest(["add_network", "--ip", "192.176.6.0",
                        "--network", "test_warn_network",
                        "--netmask", "255.255.255.0",
                        "--organization", test_org,
                        "--type", "unknown",
                        "--comments", "Made-up network"])

        # try delete org
        command = "del organization --organization %s" % test_org
        err = self.badrequesttest(command.split(" "))
        self.matchoutput(err,
                         "Bad Request: Could not delete organization %s, "
                         "networks were found using this location." % test_org,
                         command)

        # delete network
        self.noouttest(["del_network", "--ip", "192.176.6.0"])

    def test_150_delexorg1(self):
        command = "del organization --organization example"
        self.noouttest(command.split(" "))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestOrganization)
    unittest.TextTestRunner(verbosity=2).run(suite)
