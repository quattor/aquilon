#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
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
"""Module for testing the search cluster command."""

import unittest
import sys

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestSearchCluster(TestBrokerCommand):

    def testarchetypeavailable(self):
        command = "search cluster --archetype hacluster"
        out = self.commandtest(command.split(" "))

        self.matchoutput(out, "utvcs1", command)
        self.matchclean(out, "utgrid1", command)
        self.matchclean(out, "utstorage1", command)

    def testarchetypeunavailable(self):
        command = "search cluster --archetype archetype-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Archetype archetype-does-not-exist not found",
                         command)

    def testbuildstatusavailable(self):
        command = "search cluster --buildstatus build"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utvcs1", command)
        self.matchoutput(out, "utstorage2", command)
        self.matchoutput(out, "utgrid1", command)
        self.matchclean(out, "utstorages2", command)

    def testbuildstatusunavailable(self):
        command = "search cluster --buildstatus status-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "state status-does-not-exist not found",
                         command)

    def testclustertype(self):
        command = "search cluster --cluster_type compute"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utvcs1", command)
        self.matchoutput(out, "utgrid1", command)
        self.matchclean(out, "utstorage1", command)

    def testclusterandarchetype(self):
        command = ['search', 'cluster', '--archetype', 'utarchetype1',
                   '--cluster_type', 'compute']
        self.notfoundtest(command)

    def testpersonalityavailable(self):
        command = "search cluster --personality metrocluster"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utstorage1", command)
        self.matchoutput(out, "utstorage2", command)

    def testpersonalityavailable2(self):
        command = ['search', 'cluster', '--archetype', 'storagecluster',
                   '--personality', 'metrocluster']
        out = self.commandtest(command)
        self.matchoutput(out, "utstorage1", command)
        self.matchoutput(out, "utstorage2", command)
        self.matchclean(out, "utgrid1", command)

    def testpersonalityunavailable(self):
        # Will only get this error if archetype is specified
        command = ['search', 'cluster', '--archetype', 'storagecluster',
                   '--personality', 'personality-does-not-exist']
        out = self.notfoundtest(command)
        self.matchoutput(out, "Personality personality-does-not-exist, "
                         "archetype storagecluster not found.", command)

    def testpersonalityunavailable2(self):
        # Will only get an error if archetype is specified
        command = "search cluster --personality personality-does-not-exist"
        self.noouttest(command.split(" "))

    def testsandboxavailable(self):
        user = self.config.get("unittest", "user")
        command = ["search_cluster", "--sandbox=%s/utsandbox" % user]
        out = self.commandtest(command)
        self.matchoutput(out, "utstorages2", command)
        self.matchclean(out, "utstorage2", command)

    def testdomainavailable(self):
        command = ["search_cluster", "--domain=unittest"]
        out = self.commandtest(command)
        self.matchoutput(out, "utvcs1", command)
        self.matchoutput(out, "utgrid1", command)
        self.matchoutput(out, "utstorage1", command)
        self.matchoutput(out, "utstorage2", command)
        self.matchclean(out, "utstorages2", command)

    def testdomainunavailable(self):
        command = ["search_cluster", "--domain=domaind-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Domain domaind-does-not-exist not found.", command)

    def testclusterlocationavailable(self):
        command = "search cluster --cluster_building ut"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utvcs1", command)
        self.matchoutput(out, "utgrid1", command)
        self.matchoutput(out, "utstorage1", command)
        self.matchoutput(out, "utstorage2", command)
        self.matchclean(out, "utstorages2", command)  # bu

    def testclusterlocationunavailable(self):
        command = ["search_cluster",
                   "--cluster_building=building-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Building building-does-not-exist not found",
                         command)

    def testallowedpersonalityavailable(self):
        command = "search cluster --allowed_personality vulcan-1g-desktop-prod"
        out = self.commandtest(command.split(" "))

        self.matchoutput(out, "utecl1", command)

#    No Personality.get_unique in the code.
    def testallowedpersonalityunavailable(self):
        command = ['search', 'cluster',
                   '--allowed_personality', 'personality-does-not-exist']
        self.notfoundtest(command)

    def testallowedarchetypeavailable(self):
        command = "search cluster --allowed_archetype vmhost"
        out = self.commandtest(command.split(" "))

        self.matchoutput(out, "utecl1", command)

    def testallowedarchetypeunavailable(self):
        command = "search cluster --allowed_archetype archetype-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out,
                         "Archetype archetype-does-not-exist not found.",
                         command)

    def testdownhoststhreshold(self):
        command = "search cluster --down_hosts_threshold 2"
        out = self.commandtest(command.split(" "))

        self.matchoutput(out, "utecl1", command) # 2
        self.matchoutput(out, "utecl3", command) # 2
        self.matchclean(out, "utecl2", command) # 1
        self.matchclean(out, "utgrid1", command) # 5%

    def testdownhoststhresholdpercent(self):
        command = "search cluster --down_hosts_threshold 5%"
        out = self.commandtest(command.split(" "))

        self.matchoutput(out, "utgrid1", command) # 5%
        self.matchclean(out, "utecl2", command) # 1
        self.matchclean(out, "utecl3", command) #2

    def testdownmaintthreshold(self):
        command = "search cluster --down_maint_threshold 1"
        out = self.commandtest(command.split(" "))

        self.matchclean(out, "utgrid1", command) # 0
        self.matchoutput(out, "utvcs1", command) # 1
        self.matchclean(out, "utstorage1", command) # None

    def testmaxmembers(self):
        command = "search cluster --max_members 2"
        out = self.commandtest(command.split(" "))

        self.matchoutput(out, "utvcs1", command)
        self.matchclean(out, "utgrid1", command) # 2000
        self.matchoutput(out, "utstorage1", command)

    def testmemberarchetype(self):
        command = "search cluster --member_archetype vmhost"
        out = self.commandtest(command.split(" "))

        self.matchoutput(out, "utecl11", command)
        self.matchclean(out, "utgrid1", command)
        self.matchclean(out, "utstorage1", command)

    def testmemberarchetypeunavailable(self):
        command = "search cluster --member_archetype archetype-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out,
                         "Archetype archetype-does-not-exist not found.",
                         command)

    def testmemberpersonalityandarchetypeunavailable(self):
        command = ['search', 'cluster', '--member_archetype', 'filer',
                   '--member_personality', 'vulcan-1g-desktop-prod']
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Personality vulcan-1g-desktop-prod, archetype filer not found.",
                         command)

    def testmemberpersonality(self):
        command = "search cluster --member_personality vulcan-1g-desktop-prod"
        out = self.commandtest(command.split(" "))

        self.matchoutput(out, "utecl11", command)
        self.matchclean(out, "utgrid1", command)
        self.matchclean(out, "utstorage1", command)

#    No Personality.get_unique in the code.
    def testmemberpersonalityunavailable(self):
        command = ['search', 'cluster',
                   '--member_personality', 'personality-does-not-exist']
        self.notfoundtest(command)

    # based on testvmhostlocationbuilding, to see that member_ location works
    def testvmhostlocationbuilding(self):
        command = "search cluster --member_building ut"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utecl1", command)
        self.matchoutput(out, "utecl2", command)
        self.matchclean(out, "utecl3", command)
        self.matchclean(out, "utecl4", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSearchCluster)
    unittest.TextTestRunner(verbosity=5).run(suite)
