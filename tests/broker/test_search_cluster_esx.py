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
"""Module for testing the search cluster command
(former search esx cluster queries)."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestSearchClusterESX(TestBrokerCommand):

    def testclusteravailable(self):
        command = "search cluster --cluster_type esx --cluster utecl1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utecl1", command)
        self.matchclean(out, "Metacluster: utmc1", command)
        self.matchclean(out, "Building: ut", command)

    def testclusterunavailable(self):
        command = ['search', 'cluster', '--cluster_type', 'esx',
                   '--cluster', 'cluster-does-not-exist']
        self.notfoundtest(command)

    def testmetaclusteravailable(self):
        command = "search cluster --cluster_type esx --esx_metacluster utmc1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utecl1", command)
        self.matchoutput(out, "utecl2", command)
        self.matchoutput(out, "utecl3", command)
        self.matchclean(out, "utecl4", command)

    def testmetaclusterunavailable(self):
        command = ['search', 'cluster', '--cluster_type', 'esx',
                   '--esx_metacluster', 'metacluster-does-not-exist']
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Metacluster metacluster-does-not-exist not found.",
                         command)

    def testclusteravailablefull(self):
        command = ['search', 'cluster', '--cluster_type', 'esx', '--cluster',
                   'utecl1', '--fullinfo']
        out = self.commandtest(command)
        self.matchoutput(out, "ESX Cluster: utecl1", command)
        self.matchoutput(out, "Metacluster: utmc1", command)
        self.matchoutput(out, "Building: ut", command)

    def testesxhostavailable(self):
        command = ['search', 'cluster', '--cluster_type', 'esx',
                   '--member_hostname', 'evh1.aqd-unittest.ms.com']
        out = self.commandtest(command)
        self.matchoutput(out, "utecl2", command)
        self.matchclean(out, "utecl1", command)

    def testesxhostunavailable(self):
        command = ["search_cluster", "--cluster_type=esx",
                   "--member_hostname=host-does-not-exist.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Host host-does-not-exist.aqd-unittest.ms.com "
                         "not found",
                         command)

    def testvmavailable(self):
        command = "search cluster --cluster_type esx --esx_virtual_machine evm1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utecl1", command)

    def testvmunavailable(self):
        command = ['search', 'cluster', '--cluster_type', 'esx',
                   '--esx_virtual_machine', 'machine-does-not-exist']
        out = self.notfoundtest(command)
        self.matchoutput(out, "Machine machine-does-not-exist not found",
                         command)

    def testguestavailable(self):
        command = ['search', 'cluster', '--cluster_type', 'esx',
                   '--esx_guest', 'aqddesk1.msad.ms.com']
        out = self.commandtest(command)
        self.matchoutput(out, "utecl1", command)

    def testguestunavailable(self):
        command = ["search_cluster", "--cluster_type=esx",
                   "--esx_guest=host-does-not-exist.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Host host-does-not-exist.aqd-unittest.ms.com "
                         "not found",
                         command)

    # TODO we have an almost duplicate
    def testdomainavailable(self):
        command = "search cluster --cluster_type esx --domain unittest"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utecl1", command)
        self.matchoutput(out, "utecl2", command)
        self.matchoutput(out, "utecl3", command)
        self.matchoutput(out, "utecl4", command)

#    def testdomainunavailable(self):
#        command = ['search', 'cluster', '--cluster_type', 'esx',
#                   '--domain', 'domain-does-not-exist']
#        out = self.notfoundtest(command)
#        self.matchoutput(out, "Domain domain-does-not-exist not found.",
#                         command)

    def testarchetypeavailable(self):
        command = "search cluster --cluster_type esx --archetype esx_cluster"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utecl1", command)
        self.matchoutput(out, "utecl2", command)
        self.matchoutput(out, "utecl3", command)
        self.matchoutput(out, "utecl4", command)

#    def testarchetypeunavailable(self):
#        command = ['search', 'cluster', '--cluster_type', 'esx',
#                   '--archetype', 'archetype-does-not-exist']
#        out = self.notfoundtest(command)
#        self.matchoutput(out, "Archetype archetype-does-not-exist not found",
#                         command)

    # TODO we have similar test
    def testpersonalityavailable(self):
        command = "search cluster --cluster_type esx --personality esx_desktop"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utecl1", command)
        self.matchoutput(out, "utecl2", command)
        self.matchoutput(out, "utecl3", command)
        self.matchoutput(out, "utecl4", command)

    # TODO we have similar test
    def testpersonalityavailable2(self):
        command = ["search_cluster", "--cluster_type=esx",
                   "--archetype=esx_cluster", "--personality=esx_desktop"]
        out = self.commandtest(command)
        self.matchoutput(out, "utecl1", command)
        self.matchoutput(out, "utecl2", command)
        self.matchoutput(out, "utecl3", command)
        self.matchoutput(out, "utecl4", command)

#    def testpersonalityunavailable(self):
#        # Will only get this error if archetype is specified
#        command = ["search_cluster", "--cluster_type=esx",
#                   "--archetype=vmhost",
#                   "--personality=personality-does-not-exist"]
#        out = self.notfoundtest(command)
#        self.matchoutput(out, "Personality personality-does-not-exist, "
#                         "archetype vmhost not found.", command)

#    def testpersonalityunavailable2(self):
#        # Will only get an error if archetype is specified
#        command = ['search', 'cluster', '--cluster_type', 'esx',
#                   '--personality', 'personality-does-not-exist']
#        self.noouttest(command)

    def testall(self):
        command = "search cluster --cluster_type esx --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utecl1", command)
        self.matchoutput(out, "utecl2", command)
        self.matchoutput(out, "utecl3", command)
        self.matchoutput(out, "utecl4", command)

    def testallfull(self):
        command = "search cluster --cluster_type esx --all --fullinfo"
        out = self.commandtest(command.split(" "))
        # This is a good sampling, but not the full output
        self.matchoutput(out, "ESX Cluster: utecl1", command)
        self.matchoutput(out, "ESX Cluster: utecl2", command)
        self.matchoutput(out, "ESX Cluster: utecl3", command)
        self.matchoutput(out, "ESX Cluster: utecl4", command)
        self.matchoutput(out, "Metacluster: utmc1", command)
        self.matchoutput(out, "Metacluster: utmc2", command)
        self.matchoutput(out, "Building: ut", command)

    def testserviceavailable(self):
        command = ['search', 'cluster', '--cluster_type', 'esx',
                   '--service', 'esx_management_server']
        out = self.commandtest(command)
        self.matchoutput(out, "utecl1", command)
        self.matchoutput(out, "utecl2", command)
        self.matchclean(out, "utecl3", command)
        self.matchclean(out, "utecl4", command)

    def testserviceunavailable(self):
        command = ['search', 'cluster', '--cluster_type', 'esx',
                   '--service', 'service-does-not-exist']
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Service service-does-not-exist not found",
                         command)

    def testserviceinstanceavailable(self):
        command = ["search_cluster", "--cluster_type=esx",
                   "--service=esx_management_server", "--instance=ut.a"]
        out = self.commandtest(command)
        command = ["search_cluster", "--cluster_type=esx",
                   "--service=esx_management_server", "--instance=ut.b"]
        out += self.commandtest(command)
        # Which clusters are bound to either particular instance is
        # non-deterministic, but they should all be bound to one or the other.
        self.matchoutput(out, "utecl", command)

    def testserviceinstanceunavailable(self):
        command = ['search', 'cluster', '--cluster_type', 'esx',
                   '--service', 'esx_management_server',
                   '--instance', 'service-instance-does-not-exist']
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Service Instance "
                         "service-instance-does-not-exist, "
                         "service esx_management_server not found.",
                         command)

    def testinstanceavailable(self):
        command = "search cluster --cluster_type esx --instance ut.a"
        out = self.commandtest(command.split(" "))
        command = "search cluster --cluster_type esx --instance ut.b"
        out += self.commandtest(command.split(" "))
        # Which clusters are bound to either particular instance is
        # non-deterministic, but they should all be bound to one or the other.
        self.matchoutput(out, "utecl", command)

    def testinstanceunavailable(self):
        command = ["search_cluster", "--cluster_type=esx",
                   "--instance=service-instance-does-not-exist"]
        self.noouttest(command)

    def testshareavailable(self):
        command = "search cluster --cluster_type esx --esx_share test_share_1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utecl1", command)
        self.matchclean(out, "utecl2", command)
        self.matchclean(out, "utecl3", command)
        self.matchclean(out, "utecl4", command)

    def testshareunavailable(self):
        command = ['search', 'cluster', '--cluster_type', 'esx',
                   '--esx_share', 'share-does-not-exist']
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Service Instance share-does-not-exist, service "
                         "nas_disk_share not found.",
                         command)

    # Kept it since the output is different from testclusterlocationavailable
    def testesxclusterlocationavailable(self):
        command = "search cluster --cluster_type esx --cluster_building ut"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utecl1", command)
        self.matchoutput(out, "utecl2", command)
        self.matchoutput(out, "utecl3", command)
        self.matchoutput(out, "utecl4", command)

    # Removed, we have duplicate
#    def testclusterlocationunavailable(self):
#        command = ["search_cluster", "--cluster_type=esx",
#                   "--cluster_building=building-does-not-exist"]
#        out = self.notfoundtest(command)
#        self.matchoutput(out, "Building building-does-not-exist not found",
#                         command)

    def testvmhostlocationavailable(self):
        command = "search cluster --cluster_type esx --member_rack ut10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utecl1", command)
        self.matchoutput(out, "utecl2", command)
        self.matchclean(out, "utecl3", command)
        self.matchclean(out, "utecl4", command)

    def testvmhostlocationbuilding(self):
        command = "search cluster --cluster_type esx --member_building ut"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utecl1", command)
        self.matchoutput(out, "utecl2", command)
        self.matchclean(out, "utecl3", command)
        self.matchclean(out, "utecl4", command)

    def testvmhostlocationunavailable(self):
        command = ["search_cluster", "--cluster_type=esx",
                   "--member_rack=rack-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Rack rack-does-not-exist not found",
                         command)

    # TODO we have an almost duplicate, do we want this?
    def testbuildstatuspos(self):
        command = ['search_cluster', '--cluster_type=esx',
                   '--buildstatus=build']
        out = self.commandtest(command)
        self.matchoutput(out, "utecl4", command)

    def testbuildstatusneg(self):
        command = ['search_cluster', '--cluster_type=esx',
                   '--buildstatus=decommissioned']
        self.noouttest(command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSearchESXCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
