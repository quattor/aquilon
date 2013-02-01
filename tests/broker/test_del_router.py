#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012  Contributor
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
"""Module for testing the del_router command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelRouter(TestBrokerCommand):

    def testdelrouterbyip(self):
        net = self.net.tor_net[6]
        command = ["del", "router", "--ip", net.gateway]
        self.noouttest(command)

    def testdelrouterbyname(self):
        command = ["del", "router",
                   "--fqdn", "ut3gd1r01-v109-hsrp.aqd-unittest.ms.com"]
        self.noouttest(command)

    def testdelmissingrouter(self):
        net = self.net.unknown[0]
        command = ["del", "router", "--ip", net.gateway]
        out = self.notfoundtest(command)
        self.matchoutput(out, "IP address %s is not a router on network %s." %
                         (net.gateway, net.ip), command)

    def testverifyrouter(self):
        command = ["show", "router", "--all"]
        out = self.commandtest(command)
        self.matchclean(out, str(self.net.tor_net[12].gateway), command)
        self.matchclean(out, str(self.net.tor_net[6].gateway), command)

    def testdelexcx(self):
        net = self.net.unknown[0].subnet()[0]
        command = ["del", "router", "--ip", net[-2],
                   "--network_environment", "excx"]
        self.noouttest(command)

    def testdelutcolo(self):
        net = self.net.unknown[1]
        command = ["del", "router", "--ip", net[2],
                   "--network_environment", "utcolo"]
        self.noouttest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelRouter)
    unittest.TextTestRunner(verbosity=2).run(suite)
