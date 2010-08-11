#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010  Contributor
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
"""Module for testing the update metacluster command."""


import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUpdateMetaCluster(TestBrokerCommand):

    def testupdatenoop(self):
        default_max = self.config.get("broker",
                                      "metacluster_max_members_default")
        self.noouttest(["update_metacluster", "--metacluster=utmc1",
                        "--max_members=%s" % default_max])

    def testverifynoop(self):
        command = "show metacluster --metacluster utmc1"
        out = self.commandtest(command.split(" "))
        default_max = self.config.get("broker",
                                      "metacluster_max_members_default")
        self.matchoutput(out, "MetaCluster: utmc1", command)
        self.matchoutput(out, "Max members: %s" % default_max, command)
        self.matchclean(out, "Comments", command)

    def testupdateutmc2(self):
        command = ["update_metacluster", "--metacluster=utmc2",
                   "--max_members=98", "--max_shares=88",
                   "--comments", "MetaCluster with a new comment"]
        self.noouttest(command)

    def testverifyutmc2(self):
        command = "show metacluster --metacluster utmc2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "MetaCluster: utmc2", command)
        self.matchoutput(out, "Max members: 98", command)
        self.matchoutput(out, "Max shares: 88", command)
        self.matchoutput(out, "Comments: MetaCluster with a new comment",
                         command)

    def testfailmetaclustermissing(self):
        command = "update metacluster --metacluster metacluster-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out,
                         "Metacluster metacluster-does-not-exist not found",
                         command)

    def testfailreducemaxmembers(self):
        command = ["update_metacluster", "--metacluster=utmc3",
                   "--max_members=-1"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Metacluster utmc3 has 0 clusters bound, "
                         "which exceeds the requested limit -1.",
                         command)

    def testfailreducemaxshares(self):
        command = ["update_metacluster", "--metacluster=utmc1",
                   "--max_shares=6"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Metacluster utmc1 has 8 shares attached, "
                         "which exceeds the requested limit 6.",
                         command)

    def testfailhabuilding(self):
        command = ["update_metacluster", "--metacluster", "utmc1",
                   "--high_availability"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Metacluster utmc1 is over capacity regarding memory",
                         command)
        self.matchoutput(out, "but the limit is 0.", command)

    def testha(self):
        command = ["update_metacluster", "--metacluster", "utmc5",
                   "--high_availability"]
        self.noouttest(command)

    def testfailhacapacity(self):
        command = ["update_metacluster", "--metacluster", "utmc6",
                   "--high_availability"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Metacluster utmc6 is over capacity regarding memory",
                         command)

    def testverifyutmc5(self):
        command = ["show", "metacluster", "--metacluster", "utmc5"]
        (out, err) = self.successtest(command)
        self.matchoutput(out, "Capacity limits: memory: 225590", command)
        self.matchoutput(out, "Resources used by VMs: memory: 163840", command)
        self.matchoutput(out, "High availability enabled: True", command)

    def testverifyutmc6(self):
        command = ["show", "metacluster", "--metacluster", "utmc6"]
        (out, err) = self.successtest(command)
        self.matchoutput(out, "Capacity limits: memory: 451180", command)
        self.matchoutput(out, "Resources used by VMs: memory: 307200", command)
        self.matchoutput(out, "High availability enabled: False", command)

    # FIXME: Need tests for plenary templates


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateMetaCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)

