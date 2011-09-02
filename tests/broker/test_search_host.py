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
"""Module for testing the search host command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestSearchHost(TestBrokerCommand):

    def testfqdnavailable(self):
        command = "search host --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)

    def testfqdnunavailablerealdomain(self):
        command = "search host --hostname does-not-exist.one-nyp.ms.com"
        self.noouttest(command.split(" "))

    def testfqdnunavailablefakedomain(self):
        command = "search host --hostname unittest00.does-not-exist.ms.com"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "DNS Domain does-not-exist.ms.com", command)

    def testfqdnavailablefull(self):
        command = "search host --hostname unittest00.one-nyp.ms.com --fullinfo"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Primary Name: unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "Blade: ut3c1n3", command)

    def testmachineavailable(self):
        command = "search host --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)

    def testmachineunavailable(self):
        command = "search host --machine machine-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Machine machine-does-not-exist not found",
                         command)

    def testdnsdomainavailable(self):
        command = "search host --dns_domain aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest12.aqd-unittest.ms.com", command)
        self.matchclean(out, "unittest00.one-nyp.ms.com", command)

    def testdnsdomainunavailable(self):
        command = "search host --dns_domain does-not-exist.ms.com"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "DNS Domain does-not-exist.ms.com not found",
                         command)

    def testshortnameavailable(self):
        command = "search host --shortname unittest00"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)

    def testshortnameunavailable(self):
        command = "search host --shortname does-not-exist"
        self.noouttest(command.split(" "))

    def testdomainavailable(self):
        command = "search host --domain unittest"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest02.one-nyp.ms.com", command)

    def testdomainunavailable(self):
        command = "search host --domain domain-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Domain domain-does-not-exist not found",
                         command)

    def testsandboxavailable(self):
        user = self.config.get("unittest", "user")
        command = ["search_host", "--sandbox=%s/utsandbox" % user]
        out = self.commandtest(command)
        self.matchoutput(out, "server1.aqd-unittest.ms.com", command)
        self.matchclean(out, "unittest00.one-nyp.ms.com", command)

    def testbranchavailable(self):
        command = ["search_host", "--branch=utsandbox"]
        out = self.commandtest(command)
        self.matchoutput(out, "server1.aqd-unittest.ms.com", command)
        self.matchclean(out, "unittest00.one-nyp.ms.com", command)

    def testarchetypeavailable(self):
        command = "search host --archetype aquilon"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest02.one-nyp.ms.com", command)

    def testarchetypeunavailable(self):
        command = "search host --archetype archetype-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Archetype archetype-does-not-exist not found",
                         command)

    def testbuildstatusavailable(self):
        command = "search host --buildstatus ready"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest02.one-nyp.ms.com", command)
        self.matchoutput(out, self.aurora_with_node, command)
        self.matchoutput(out, self.aurora_without_node, command)

    def testbuildstatusunavailable(self):
        command = "search host --buildstatus status-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "state status-does-not-exist not found",
                         command)

    def testipavailable(self):
        command = "search host --ip %s" % self.net.unknown[0].usable[2]
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)

    def testipunavailable(self):
        command = "search host --ip 199.98.16.4"
        self.noouttest(command.split(" "))

    def testipbad(self):
        command = "search host --ip not-an-ip-address"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out,
                         "Expected an IPv4 address for --ip: "
                         "not-an-ip-address",
                         command)

    def testnetworkipavailable(self):
        command = "search host --networkip %s" % self.net.unknown[0].ip
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)
        self.matchclean(out, "unittest00-e1.one-nyp.ms.com", command)
        self.matchclean(out, "unittest00r.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest01.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest02.one-nyp.ms.com", command)
        self.matchclean(out, "unittest02rsa.one-nyp.ms.com", command)

    def testnetworkipunavailable(self):
        command = "search host --networkip 199.98.16.0"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Network with address 199.98.16.0 not found",
                         command)

    def testmacavailable(self):
        command = "search host --mac %s" % self.net.unknown[0].usable[2].mac
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)

    def testmacunavailable(self):
        command = "search host --mac 02:02:c7:62:10:04"
        self.noouttest(command.split(" "))

    def testall(self):
        command = "search host --all"
        out = self.commandtest(command.split(" "))
        # This is a good sampling, but not the full output
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)
        self.matchclean(out, "unittest00r.one-nyp.ms.com", command)
        self.matchclean(out, "unittest00-e1.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest01.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest02.one-nyp.ms.com", command)
        self.matchclean(out, "unittest02rsa.one-nyp.ms.com", command)
        self.matchoutput(out, self.aurora_with_node, command)
        self.matchoutput(out, self.aurora_without_node, command)
        self.matchclean(out, "ut3gd1r01.aqd-unittest.ms.com", command)
        self.matchclean(out, "ut3c1.aqd-unittest.ms.com", command)

    def testallfull(self):
        command = "search host --all --fullinfo"
        out = self.commandtest(command.split(" "))
        # This is a good sampling, but not the full output
        self.matchoutput(out, "Primary Name: unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest00r.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest00-e1.one-nyp.ms.com", command)
        self.matchoutput(out, "Primary Name: unittest01.one-nyp.ms.com", command)
        self.matchoutput(out, "Primary Name: unittest02.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest02rsa.one-nyp.ms.com", command)
        self.matchoutput(out, "Primary Name: %s" % self.aurora_with_node, command)
        self.matchoutput(out, "Primary Name: %s" % self.aurora_without_node,
                         command)

    def testpersonalityavailable(self):
        command = "search host --personality compileserver"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest02.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)

    def testpersonalityavailable2(self):
        command = "search host --archetype aquilon --personality compileserver"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest02.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)
        self.matchclean(out, "aquilon86.aqd-unittest.ms.com", command)

    def testpersonalityunavailable(self):
        # Will only get this error if archetype is specified
        command = "search host --archetype aquilon --personality personality-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Personality personality-does-not-exist, "
                         "archetype aquilon not found.", command)

    def testpersonalityunavailable2(self):
        # Will only get an error if archetype is specified
        command = "search host --personality personality-does-not-exist"
        self.noouttest(command.split(" "))

    def testosavailable(self):
        command = "search host --osname linux --osversion 5.0.1-x86_64 --archetype aquilon"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest02.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)

    def testosunavailable(self):
        command = "search host --osname os-does-not-exist --osversion foo --archetype aquilon"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Operating System os-does-not-exist, "
                         "version foo, archetype aquilon not found.", command)

    def testosnameonly(self):
        command = "search host --osname linux"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest02.one-nyp.ms.com", command)

    def testosversiononly(self):
        command = "search host --osversion 5.0.1-x86_64"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)

    def testserviceavailable(self):
        command = "search host --service utsvc"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest02.one-nyp.ms.com", command)

    def testserviceunavailable(self):
        command = "search host --service service-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Service service-does-not-exist not found",
                         command)

    def testserviceinstanceavailable(self):
        command = "search host --service utsvc --instance utsi1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)
        self.matchclean(out, "unittest02.one-nyp.ms.com", command)

    def testserviceinstanceunavailable(self):
        command = "search host --service utsvc " \
                  "--instance service-instance-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Service utsvc, instance "
                              "service-instance-does-not-exist not found",
                         command)

    def testinstanceavailable(self):
        command = "search host --instance utsi1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)
        self.matchclean(out, "unittest02.one-nyp.ms.com", command)

    def testinstanceunavailable(self):
        command = "search host --instance service-instance-does-not-exist"
        self.noouttest(command.split(" "))

    def testserverofservice00(self):
        """search host by server of service provided """
        self.noouttest(["add", "service", "--service", "foo",
                        "--instance", "fooinst1"])

        self.noouttest(["add", "service", "--service", "foo",
                        "--instance", "fooinst2"])

        self.noouttest(["add", "service", "--service", "baa",
                        "--instance", "fooinst1"])

        self.noouttest(["bind", "server",
                        "--hostname", "unittest00.one-nyp.ms.com",
                        "--service", "foo", "--instance", "fooinst1"])

        self.noouttest(["bind", "server",
                        "--hostname", "unittest01.one-nyp.ms.com",
                        "--service", "foo", "--instance", "fooinst2"])

        self.noouttest(["bind", "server",
                        "--hostname", "unittest02.one-nyp.ms.com",
                        "--service", "baa", "--instance", "fooinst1"])

        command = "search host --server_of_service foo"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest01.one-nyp.ms.com", command)

    def testserverofserviceunavailable(self):
        """ search host for a service which is not defined """
        command = "search host --server_of_service service-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Service service-does-not-exist not found",
                         command)

    def testserverofservice01(self):
        """ search host for a defined service and instance """
        command = "search host --server_of_service foo " \
                  "--server_of_instance fooinst1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)

    def testserverofservice02(self):
        """ search host for a defined instance """
        command = "search host --server_of_instance fooinst1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest02.one-nyp.ms.com", command)

    def testserverofservice03(self):
        """" search host for a defined service with undefined instance """
        command = "search host --server_of_service foo " \
                  "--server_of_instance service-instance-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Service foo, instance "
                              "service-instance-does-not-exist not found",
                         command)

    def testserverofinstanceunavailable(self):
        """search host for a undefined instance """
        command = "search host --server_of_instance " \
                  "service-instance-does-not-exist"
        self.noouttest(command.split(" "))

    def testserverofservice04(self):
        """search host for a defined service but no servers assigned"""
        self.noouttest(["unbind", "server",
            "--hostname", "unittest01.one-nyp.ms.com",
            "--service", "foo", "--instance", "fooinst2"])

        self.noouttest(["search", "host",
                        "--server_of_service",  "foo", "--server_of_instance", "fooinst2"])

        self.noouttest(["search", "host", "--server_of_instance", "fooinst2"])

    def testserverofservice05(self):
        """search host for a defined service but no servers assigned """
        self.noouttest(["unbind", "server",
                        "--hostname", "unittest00.one-nyp.ms.com",
                        "--service", "foo", "--instance", "fooinst1"])

        self.noouttest(["unbind", "server",
                        "--hostname", "unittest02.one-nyp.ms.com",
                        "--service", "baa", "--instance", "fooinst1"])

        command = "search host --server_of_service foo"

        self.noouttest(command.split(" "))

        ## cleanup
        self.noouttest(["del", "service","--service",
                        "foo", "--instance", "fooinst1"])

        self.noouttest(["del", "service", "--service",
                        "foo", "--instance", "fooinst2"])

        self.noouttest(["del", "service", "--service", "foo"])

        self.noouttest(["del", "service", "--service",
                        "baa", "--instance", "fooinst1"])

        self.noouttest(["del", "service", "--service", "baa"])

    def testmodelavailable(self):
        command = "search host --model vb1205xm"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest15.aqd-unittest.ms.com", command)
        self.matchoutput(out, "unittest16.aqd-unittest.ms.com", command)
        self.matchoutput(out, "unittest17.aqd-unittest.ms.com", command)

    def testmodellocation(self):
        # Utilize two filters on the same table
        command = "search host --model vb1205xm --building ut"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest15.aqd-unittest.ms.com", command)
        self.matchoutput(out, "unittest16.aqd-unittest.ms.com", command)
        self.matchoutput(out, "unittest17.aqd-unittest.ms.com", command)

    def testmodelunavailable(self):
        command = "search host --model model-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Model model-does-not-exist not found.",
                         command)

    def testmodelvendorconflict(self):
        command = "search host --model vb1205xm --vendor dell"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Model vb1205xm, vendor dell not found.",
                         command)

    def testmodelmachinetypeconflict(self):
        command = "search host --model vb1205xm --machine_type virtual_machine"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Model vb1205xm, machine_type "
                         "virtual_machine not found.", command)

    def testvendoravailable(self):
        command = "search host --vendor dell"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest12.aqd-unittest.ms.com", command)

    def testvendorunavailable(self):
        command = "search host --vendor vendor-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Vendor vendor-does-not-exist not found",
                         command)

    def testmachinetypeavailable(self):
        command = "search host --machine_type rackmount"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest12.aqd-unittest.ms.com", command)

    def testmachinetypeunavailable(self):
        command = "search host --machine_type machine_type-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Model machine_type "
                         "machine_type-does-not-exist not found.", command)

    def testserialavailable(self):
        command = "search host --serial 99C5553"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest02.one-nyp.ms.com", command)

    def testserialunavailable(self):
        command = "search host --serial serial-does-not-exist"
        self.noouttest(command.split(" "))

    def testlocationavailable(self):
        command = "search host --rack ut3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest01.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest02.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest12.aqd-unittest.ms.com", command)

    def testlocationbuilding(self):
        command = "search host --building ut"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest01.one-nyp.ms.com", command)
        self.matchoutput(out, "aquilon61.aqd-unittest.ms.com", command)
        self.matchoutput(out, "server1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "evh1.aqd-unittest.ms.com", command)

    def testlocationcampus(self):
        command = "search host --campus ny"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest01.one-nyp.ms.com", command)
        self.matchoutput(out, "aquilon61.aqd-unittest.ms.com", command)
        self.matchoutput(out, "server1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "evh1.aqd-unittest.ms.com", command)

    def testlocationcomplex(self):
        command = "search host --building ut --personality inventory"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "unittest12.aqd-unittest.ms.com", command)
        self.matchoutput(out, "aquilon61.aqd-unittest.ms.com", command)
        self.matchoutput(out, "server1.aqd-unittest.ms.com", command)
        self.matchclean(out, "evh1.aqd-unittest.ms.com", command)

    def testlocationunavailable(self):
        command = "search host --building building-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Building building-does-not-exist not found",
                         command)

    def testclusteravailable(self):
        command = "search host --cluster utecl1"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "evh1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "evh2.aqd-unittest.ms.com", command)
        self.matchoutput(out, "evh3.aqd-unittest.ms.com", command)
        self.matchoutput(out, "evh4.aqd-unittest.ms.com", command)

    def testclusterunavailable(self):
        command = "search host --cluster cluster-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Cluster cluster-does-not-exist not found",
                         command)

    def testclusterunavailablefull(self):
        command = "search host --fullinfo --cluster cluster-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Cluster cluster-does-not-exist not found",
                         command)

    def testguestoncluster(self):
        command = "search host --guest_on_cluster utecl5"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ivirt1.aqd-unittest.ms.com", command)
        self.matchclean(out, "ivirt4.aqd-unittest.ms.com", command)

    def testguestonshare(self):
        command = "search host --guest_on_share utecl5_share"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ivirt1.aqd-unittest.ms.com", command)
        self.matchclean(out, "ivirt4.aqd-unittest.ms.com", command)

    def testprotobuf(self):
        command = "search host --hostname unittest02.one-nyp.ms.com --format proto"
        out = self.commandtest(command.split(" "))
        self.parse_hostlist_msg(out, expect=1)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSearchHost)
    unittest.TextTestRunner(verbosity=5).run(suite)
