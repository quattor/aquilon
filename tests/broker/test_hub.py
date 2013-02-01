#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2013  Contributor
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
"""Module for testing the add/del/show hub command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestHub(TestBrokerCommand):

    def testaddhub(self):
        command = ["add", "hub", "--hub", "hub1", "--fullname",
                   "hub1 example", "--comments", "test hub1"]
        self.noouttest(command)

        command = ["add", "organization", "--organization", "example",
                   "--fullname", "Example, Inc"]
        self.noouttest(command)

        command = ["add", "hub", "--hub", "hub2", "--fullname", "hub2 example",
                   "--organization", "example", "--comments", "test hub2"]
        self.noouttest(command)

    def testaddhubshow(self):
        command = "show hub --hub hub1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hub: hub1", command)
        self.matchoutput(out, "  Fullname: hub1 example", command)
        self.matchoutput(out, "  Comments: test hub1", command)
        self.matchoutput(out, "  Location Parents: [Organization ms]", command)

        command = "show hub --hub hub2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hub: hub2", command)
        self.matchoutput(out, "  Fullname: hub2 example", command)
        self.matchoutput(out, "  Comments: test hub2", command)
        self.matchoutput(out, "  Location Parents: [Organization example]",
                         command)

        command = "show hub --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hub: hub1", command)
        self.matchoutput(out, "Hub: hub2", command)

    def testverifydelhub(self):
        command = "show hub --hub hub1"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Hub hub1 not found.", command)

        command = "show hub --hub hub2"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Hub hub2 not found.", command)

        command = "show hub --all"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Hub: hub1", command)
        self.matchclean(out, "Hub: hub2", command)

    def testdelhub(self):
        test_hub = "hub1"

        # add network to hub
        self.noouttest(["add_network", "--ip", "192.176.6.0",
                        "--network", "test_warn_network",
                        "--netmask", "255.255.255.0",
                        "--hub", test_hub,
                        "--type", "unknown",
                        "--comments", "Made-up network"])

        # try delete hub
        command = "del hub --hub %s" % test_hub
        err = self.badrequesttest(command.split(" "))
        self.matchoutput(err,
                         "Bad Request: Could not delete hub %s, networks "
                         "were found using this location." % test_hub,
                         command)

        # delete network
        self.noouttest(["del_network", "--ip", "192.176.6.0"])

    def testdelhub01(self):
        command = "del hub --hub hub1"
        self.noouttest(command.split(" "))

        ## delete hub1 again
        command = "del hub --hub hub1"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Hub hub1 not found.", command)

    def testdelhub02(self):
        command = "del hub --hub hub2"
        self.noouttest(command.split(" "))

        ## delete hub2 again
        command = "del hub --hub hub2"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Hub hub2 not found.", command)

        command = "del organization --organization example"
        self.noouttest(command.split(" "))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestHub)
    unittest.TextTestRunner(verbosity=2).run(suite)
