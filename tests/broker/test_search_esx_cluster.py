#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010,2011  Contributor
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
"""Module for testing the search esx cluster command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestSearchESXCluster(TestBrokerCommand):

    def testclusteravailable(self):
        command = "search esx cluster --cluster utecl1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utecl1", command)
        self.matchclean(out, "Metacluster: utmc1", command)
        self.matchclean(out, "Building: ut", command)

    def testclusterunavailable(self):
        command = "search esx cluster --cluster cluster-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out,
                         "ESX Cluster cluster-does-not-exist not found.",
                         command)

    def testmetaclusteravailable(self):
        command = "search esx cluster --metacluster utmc1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utecl1", command)
        self.matchoutput(out, "utecl2", command)
        self.matchoutput(out, "utecl3", command)
        self.matchclean(out, "utecl4", command)

    def testmetaclusterunavailable(self):
        command = "search esx cluster --metacluster metacluster-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out,
                         "Metacluster metacluster-does-not-exist not found.",
                         command)

    def testclusteravailablefull(self):
        command = "search esx cluster --cluster utecl1 --fullinfo"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ESX Cluster: utecl1", command)
        self.matchoutput(out, "Metacluster: utmc1", command)
        self.matchoutput(out, "Building: ut", command)

    def testesxhostavailable(self):
        command = "search esx cluster --esx_hostname evh1.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utecl2", command)
        self.matchclean(out, "utecl1", command)

    def testesxhostunavailable(self):
        command = ["search_esx_cluster",
                   "--esx_hostname=host-does-not-exist.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Host host-does-not-exist.aqd-unittest.ms.com "
                         "not found",
                         command)

    def testvmavailable(self):
        command = "search esx cluster --virtual_machine evm1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utecl1", command)

    def testvmunavailable(self):
        command = "search esx cluster --virtual_machine machine-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Machine machine-does-not-exist not found",
                         command)

    def testguestavailable(self):
        command = "search esx cluster --guest aqddesk1.msad.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utecl1", command)

    def testguestunavailable(self):
        command = ["search_esx_cluster",
                   "--guest=host-does-not-exist.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Host host-does-not-exist.aqd-unittest.ms.com "
                         "not found",
                         command)

    def testdomainavailable(self):
        command = "search esx cluster --domain unittest"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utecl1", command)
        self.matchoutput(out, "utecl2", command)
        self.matchoutput(out, "utecl3", command)
        self.matchoutput(out, "utecl4", command)

    def testdomainunavailable(self):
        command = "search esx cluster --domain domain-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Domain domain-does-not-exist not found.",
                         command)

    def testarchetypeavailable(self):
        command = "search esx cluster --archetype vmhost"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utecl1", command)
        self.matchoutput(out, "utecl2", command)
        self.matchoutput(out, "utecl3", command)
        self.matchoutput(out, "utecl4", command)

    def testarchetypeunavailable(self):
        command = "search esx cluster --archetype archetype-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Archetype archetype-does-not-exist not found",
                         command)

    def testpersonalityavailable(self):
        command = "search esx cluster --personality esx_desktop"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utecl1", command)
        self.matchoutput(out, "utecl2", command)
        self.matchoutput(out, "utecl3", command)
        self.matchoutput(out, "utecl4", command)

    def testpersonalityavailable2(self):
        command = ["search_esx_cluster", "--archetype=vmhost",
                   "--personality=esx_desktop"]
        out = self.commandtest(command)
        self.matchoutput(out, "utecl1", command)
        self.matchoutput(out, "utecl2", command)
        self.matchoutput(out, "utecl3", command)
        self.matchoutput(out, "utecl4", command)

    def testpersonalityunavailable(self):
        # Will only get this error if archetype is specified
        command = ["search_esx_cluster", "--archetype=vmhost",
                   "--personality=personality-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Personality personality-does-not-exist, "
                         "archetype vmhost not found.", command)

    def testpersonalityunavailable2(self):
        # Will only get an error if archetype is specified
        command = "search esx cluster --personality personality-does-not-exist"
        self.noouttest(command.split(" "))

    def testall(self):
        command = "search esx cluster --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utecl1", command)
        self.matchoutput(out, "utecl2", command)
        self.matchoutput(out, "utecl3", command)
        self.matchoutput(out, "utecl4", command)

    def testallfull(self):
        command = "search esx cluster --all --fullinfo"
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
        command = "search esx cluster --service esx_management_server"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utecl1", command)
        self.matchoutput(out, "utecl2", command)
        self.matchclean(out, "utecl3", command)
        self.matchclean(out, "utecl4", command)

    def testserviceunavailable(self):
        command = "search esx cluster --service service-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out,
                         "Service service-does-not-exist not found",
                         command)

    def testserviceinstanceavailable(self):
        command = ["search_esx_cluster", "--service=esx_management_server",
                   "--instance=ut.a"]
        out = self.commandtest(command)
        command = ["search_esx_cluster", "--service=esx_management_server",
                   "--instance=ut.b"]
        out += self.commandtest(command)
        # Which clusters are bound to either particular instance is
        # non-deterministic, but they should all be bound to one or the other.
        self.matchoutput(out, "utecl", command)

    def testserviceinstanceunavailable(self):
        command = "search esx cluster --service esx_management_server " \
                  "--instance service-instance-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out,
                         "ServiceInstance with name of "
                         "service-instance-does-not-exist and "
                         "Service esx_management_server not found.",
                         command)

    def testinstanceavailable(self):
        command = "search esx cluster --instance ut.a"
        out = self.commandtest(command.split(" "))
        command = "search esx cluster --instance ut.b"
        out += self.commandtest(command.split(" "))
        # Which clusters are bound to either particular instance is
        # non-deterministic, but they should all be bound to one or the other.
        self.matchoutput(out, "utecl", command)

    def testinstanceunavailable(self):
        command = ["search_esx_cluster",
                   "--instance=service-instance-does-not-exist"]
        self.noouttest(command)

    def testshareavailable(self):
        command = "search esx cluster --share test_share_1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utecl1", command)
        self.matchclean(out, "utecl2", command)
        self.matchclean(out, "utecl3", command)
        self.matchclean(out, "utecl4", command)

    def testserviceinstanceunavailable(self):
        command = "search esx cluster --share share-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out,
                         "Service Instance share-does-not-exist, service "
                         "nas_disk_share not found.",
                         command)

    def testclusterlocationavailable(self):
        command = "search esx cluster --cluster_building ut"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utecl1", command)
        self.matchoutput(out, "utecl2", command)
        self.matchoutput(out, "utecl3", command)
        self.matchoutput(out, "utecl4", command)

    def testclusterlocationunavailable(self):
        command = ["search_esx_cluster",
                   "--cluster_building=building-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Building building-does-not-exist not found",
                         command)

    def testvmhostlocationavailable(self):
        command = "search esx cluster --vmhost_rack ut10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utecl1", command)
        self.matchoutput(out, "utecl2", command)
        self.matchclean(out, "utecl3", command)
        self.matchclean(out, "utecl4", command)

    def testvmhostlocationbuilding(self):
        command = "search esx cluster --vmhost_building ut"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utecl1", command)
        self.matchoutput(out, "utecl2", command)
        self.matchclean(out, "utecl3", command)
        self.matchclean(out, "utecl4", command)

    def testvmhostlocationunavailable(self):
        command = ["search_esx_cluster",
                   "--vmhost_rack=rack-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Rack rack-does-not-exist not found",
                         command)

    def testbuildstatuspos(self):
        command = ['search_esx_cluster', '--buildstatus=build']
        out = self.commandtest(command)
        self.matchoutput(out, "utecl4", command)

    def testbuildstatusneg(self):
        command = ['search_esx_cluster', '--buildstatus=decommissioned']
        self.noouttest(command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSearchESXCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
