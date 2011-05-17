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
"""Module for testing the update network command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUpdateNetwork(TestBrokerCommand):

    def test_100_update_discoverable(self):
        self.noouttest(["update", "network", "--ip", "10.184.78.224",
                        "--discoverable"])

    def test_110_verify_discoverable(self):
        command = "show network --ip 10.184.78.224"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Discoverable: True", command)

    def test_200_update_nodiscoverable(self):
        self.noouttest(["update", "network", "--ip", "10.184.78.224",
                        "--nodiscoverable"])

    def test_210_verify_nodiscoverable(self):
        command = "show network --ip 10.184.78.224"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Discoverable: False", command)

    def test_300_update_noenv(self):
        command = ["update", "network", "--network", "excx-net",
                   "--discoverable"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Network excx-net not found.", command)

    def test_310_update_withenv(self):
        command = ["update", "network", "--network", "excx-net",
                   "--discoverable", "--network_environment", "excx"]
        self.noouttest(command)

    def test_315_verify(self):
        command = ["show", "network", "--network", "excx-net",
                   "--network_environment", "excx"]
        out = self.commandtest(command)
        self.matchoutput(out, "Discoverable: True", command)

    # There should be a test_constraint_network.py one day...
    def test_900_delinuse(self):
        net = self.net.unknown[0]
        command = ["del", "network", "--ip", net.ip]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Network %s is still in use" % net.ip, command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateDomain)
    unittest.TextTestRunner(verbosity=2).run(suite)

