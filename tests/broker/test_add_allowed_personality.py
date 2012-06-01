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
"""Module for testing the add allowed_personality commands."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.6"))

from brokertest import TestBrokerCommand


class TestAddAllowedPersonality(TestBrokerCommand):

    def test_10_addbadconstraint(self):
        command = ["add_allowed_personality", "--archetype", "vmhost",
                   "--personality=generic", "--cluster=utecl1"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The cluster member evh1.aqd-unittest.ms.com "
                         "has a personality of vulcan-1g-desktop-prod which is "
                         "incompatible", command)

    def test_12_failmissingcluster(self):
        command = ["add_allowed_personality", "--archetype", "vmhost",
                   "--personality=vulcan-1g-desktop-prod", "--cluster=does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Cluster does-not-exist not found.",
                         command)

    def test_14_failmissingcluster(self):
        command = ["add_allowed_personality", "--archetype", "vmhost",
                   "--personality=does-not-exist", "--cluster=utecl1"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Personality does-not-exist, "
                         "archetype vmhost not found.",
                         command)

    def test_15_addconstraint(self):
        self.successtest(["add_allowed_personality",
                          "--archetype", "vmhost",
                          "--personality=vulcan-1g-desktop-prod",
                          "--cluster", "utecl1"])
        self.successtest(["add_allowed_personality",
                          "--archetype", "vmhost",
                          "--personality=generic",
                          "--cluster", "utecl1"])

    def test_20_checkconstraint(self):
        command = ["show_cluster", "--cluster=utecl1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Allowed Personality: Personality vmhost/vulcan-1g-desktop-prod", command)
        self.matchoutput(out, "Allowed Personality: Personality vmhost/generic", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddAllowedPersonality)
    unittest.TextTestRunner(verbosity=2).run(suite)
