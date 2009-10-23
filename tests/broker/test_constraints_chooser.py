#!/usr/bin/env python2.5
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009  Contributor
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
"""Testing constraints in the reconfigure section was getting unweildy."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestChooserConstraints(TestBrokerCommand):

    def test_000_setupservice(self):
        command = "add service --service chooser_test --instance max_clients"
        self.noouttest(command.split(" "))

        command = ["update_service", "--service=chooser_test",
                   "--instance=max_clients", "--max_clients=1"]
        self.noouttest(command)

        command = ["map_service", "--service=chooser_test",
                   "--instance=max_clients", "--building=ut"]
        self.noouttest(command)

    def test_010_setuphost(self):
        # Bind a host to that instance
        command = ["bind_client", "--hostname=aquilon61.aqd-unittest.ms.com",
                   "--service=chooser_test", "--instance=max_clients"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "aquilon61.aqd-unittest.ms.com adding binding for "
                         "service chooser_test instance max_clients",
                         command)

    def test_100_failmaxclients(self):
        # Try to bind a second host to that instance
        command = ["bind_client", "--hostname=aquilon62.aqd-unittest.ms.com",
                   "--service=chooser_test", "--instance=max_clients"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The available instances ['max_clients'] for service "
                         "chooser_test are at full capacity.",
                         command)

    def test_110_rebind(self):
        # Rebind the first host - should be no change/errors
        # This is for coverage to check the edge condition.
        command = ["rebind_client", "--hostname=aquilon61.aqd-unittest.ms.com",
                   "--service=chooser_test"]
        out = self.commandtest(command)
        self.matchclean(out, "removing binding", command)
        self.matchclean(out, "adding binding", command)

    def test_120_verifyrebind(self):
        command = ["show_host", "--hostname=aquilon61.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Template: service/chooser_test/max_clients",
                         command)

    def test_200_cleanuphost(self):
        command = ["reconfigure", "--hostname=aquilon61.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "aquilon61.aqd-unittest.ms.com removing binding for "
                         "service chooser_test instance max_clients",
                         command)

    def test_210_cleanupservice(self):
        command = ["unmap_service", "--archetype=aquilon", "--building=ut",
                   "--service=chooser_test", "--instance=max_clients"]
        self.noouttest(command)

        command = "del service --service chooser_test --instance max_clients"
        self.noouttest(command.split(" "))

        command = "del service --service chooser_test"
        self.noouttest(command.split(" "))


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(
        TestChooserConstraints)
    unittest.TextTestRunner(verbosity=2).run(suite)
