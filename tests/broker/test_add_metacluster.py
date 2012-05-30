#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
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
"""Module for testing the add metacluster command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddMetaCluster(TestBrokerCommand):

    def testaddutmc1(self):
        command = ["add_metacluster", "--metacluster=utmc1", "--max_shares=8",
                   "--domain=ut-prod", "--building=ut"]
        self.noouttest(command)

    def testverifyutmc1(self):
        command = "show metacluster --metacluster utmc1"
        out = self.commandtest(command.split(" "))
        default_members = self.config.get("broker",
                                          "metacluster_max_members_default")
        self.matchoutput(out, "MetaCluster: utmc1", command)
        self.matchoutput(out, "Max members: %s" % default_members, command)
        self.matchoutput(out, "Max shares: 8", command)
        self.matchclean(out, "Comments", command)
        self.matchclean(out, "Member:", command)
        self.matchclean(out, "Share:", command)

    def testfailaddexisting(self):
        command = ["add_metacluster", "--metacluster=utmc1",
                   "--building=ut", "--domain=ut-prod"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Metacluster utmc1 already exists.", command)

    def testaddutmc2(self):
        command = ["add_metacluster", "--metacluster=utmc2",
                   "--max_members=99", "--max_shares=89", "--building=ut",
                   "--domain=ut-prod",
                   "--comments", "MetaCluster with a comment"]
        self.noouttest(command)

    def testverifyutmc2(self):
        command = "show metacluster --metacluster utmc2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "MetaCluster: utmc2", command)
        self.matchoutput(out, "Max members: 99", command)
        self.matchoutput(out, "Max shares: 89", command)
        self.matchoutput(out, "Comments: MetaCluster with a comment", command)

    def testaddutmc3(self):
        command = ["add_metacluster", "--metacluster=utmc3",
                   "--max_members=0", "--building=ut", "--domain=ut-prod",
                   "--comments", "MetaCluster with no members allowed"]
        self.noouttest(command)

    def testverifyutmc3(self):
        default_shares = self.config.get("broker",
                                         "metacluster_max_shares_default")
        command = "show metacluster --metacluster utmc3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "MetaCluster: utmc3", command)
        self.matchoutput(out, "Max members: 0", command)
        self.matchoutput(out, "Max shares: %s" % default_shares, command)
        self.matchoutput(out, "Comments: MetaCluster with no members allowed",
                         command)

    def testaddutmc4(self):
        # Sort of a mini-10 Gig design for port group testing...
        command = ["add_metacluster", "--metacluster=utmc4",
                   "--max_members=6", "--max_shares=7", "--building=ut",
                   "--domain=ut-prod"]
        self.noouttest(command)

    def testaddutmc5(self):
        # High availability testing
        command = ["add_metacluster", "--metacluster=utmc5",
                   "--max_members=6", "--max_shares=6", "--building=ut",
                   "--domain=ut-prod"]
        self.noouttest(command)

    def testaddutmc6(self):
        # High availability testing
        command = ["add_metacluster", "--metacluster=utmc6",
                   "--max_members=6", "--max_shares=6", "--building=ut",
                   "--domain=ut-prod"]
        self.noouttest(command)

    def testaddutmc7(self):
        # Test moving machines between metaclusters
        command = ["add_metacluster", "--metacluster=utmc7", "--building=ut",
                   "--domain=ut-prod"]
        self.noouttest(command)

    def testaddvulcan1(self):
        # this should be removed when virtbuild supports new options
        command = ["add_metacluster", "--metacluster=vulcan1"]
        self.noouttest(command)

    def testverifyshowall(self):
        command = "show metacluster --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "MetaCluster: utmc1", command)
        self.matchoutput(out, "MetaCluster: utmc2", command)
        self.matchoutput(out, "MetaCluster: utmc3", command)

    def testnotfoundmetacluster(self):
        command = "show metacluster --metacluster metacluster-does-not-exist"
        self.notfoundtest(command.split(" "))

    def testfailglobal(self):
        command = ["add_metacluster", "--metacluster=global", "--building=ut",
                   "--domain=ut-prod"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "name global is reserved", command)

    def testbadlocation(self):
        command = ["add_metacluster", "--metacluster=uscluster",
                   "--country=us"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Country us is not within "
                         "a campus.", command)

if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddMetaCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)

