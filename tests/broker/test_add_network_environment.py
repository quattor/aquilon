#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011,2012  Contributor
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
"""Module for testing the add_network_environment command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddNetworkEnvironment(TestBrokerCommand):

    def testaddexcx(self):
        command = ["add", "network", "environment",
                   "--network_environment", "excx", "--building", "np",
                   "--dns_environment", "excx",
                   "--comments", "Exchange X"]
        self.noouttest(command)

    def testaddutcolo(self):
        command = ["add", "network", "environment",
                   "--network_environment", "utcolo",
                   "--dns_environment", "ut-env",
                   "--comments", "Unit test colo environment"]
        self.noouttest(command)

    def testaddcardenv(self):
        command = ["add", "network", "environment",
                   "--network_environment", "cardenv",
                   "--dns_environment", "ut-env",
                   "--comments", "Card network environment"]
        self.noouttest(command)

    def testaddbadname(self):
        command = ["add", "network", "environment",
                   "--dns_environment", "ut-env",
                   "--network_environment", "<badname>"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "'<badname>' is not a valid value for network environment",
                         command)

    def testverifyexcx(self):
        command = ["show", "network", "environment",
                   "--network_environment", "excx"]
        out = self.commandtest(command)
        self.matchoutput(out, "Network Environment: excx", command)
        self.matchoutput(out, "Building: np", command)
        self.matchoutput(out, "Comments: Exchange X", command)

    def testverifyutcolo(self):
        command = ["show", "network", "environment",
                   "--network_environment", "utcolo"]
        out = self.commandtest(command)
        self.matchoutput(out, "Network Environment: utcolo", command)
        self.matchclean(out, "Building:", command)
        self.matchoutput(out, "Comments: Unit test colo environment", command)

    def testshowall(self):
        command = ["show", "network", "environment", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Network Environment: internal", command)
        self.matchoutput(out, "Network Environment: excx", command)
        self.matchoutput(out, "Network Environment: utcolo", command)

    def testinternal(self):
        command = ["add", "network", "environment",
                   "--network_environment", "not-internal",
                   "--dns_environment", "internal"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Only the default network environment may be "
                         "associated with the default DNS environment.",
                         command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddNetworkEnvironment)
    unittest.TextTestRunner(verbosity=2).run(suite)
