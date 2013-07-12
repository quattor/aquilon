#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2012  Contributor
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
"""Module for testing the vulcan2 related commands."""

import os
import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand

# see test_vulcan2.py
class TestVulcanLocalDisk(TestBrokerCommand):

    metacluster = "utmc9"
    cluster = "utlccl1"
    switch = "utpgsw1.aqd-unittest.ms.com"
    vmhost = "utpgh0.aqd-unittest.ms.com"
    machine = "utpgs01p0"

    def getip(self):
        return self.net.unknown[18].usable[0]

    def test_000_add_vlocal(self):
        # vmhost archetype
        command = ["add_personality", "--archetype", "vmhost",
                   "--personality", "vulcan-local-disk",
                   "--host_environment=dev",
                   "--grn", "grn:/ms/ei/aquilon/aqd"]
        self.noouttest(command)

        command = ["add_required_service", "--service", "esx_management_server",
                   "--personality", "vulcan-local-disk",
                   "--archetype", "vmhost"]
        self.noouttest(command)

        command = ["map", "service", "--service", "esx_management_server", "--instance", "ut.a",
                   "--building", "ut", "--personality", "vulcan-local-disk",
                   "--archetype", "vmhost"]
        self.noouttest(command)

        command = ["add_personality", "--archetype", "esx_cluster",
                   "--personality", "vulcan-local-disk",
                   "--host_environment=dev",
                   "--grn", "grn:/ms/ei/aquilon/aqd"]
        self.noouttest(command)

        command = ["add_required_service", "--service", "esx_management_server",
                   "--personality", "vulcan-local-disk",
                   "--archetype", "esx_cluster"]
        self.noouttest(command)

        command = ["map", "service", "--service", "esx_management_server", "--instance", "ut.a",
                   "--building", "ut", "--personality", "vulcan-local-disk",
                   "--archetype", "esx_cluster"]
        self.noouttest(command)

    def test_005_addutmc9(self):
        command = ["add_metacluster", "--metacluster=%s" % self.metacluster,
                   "--personality=vulcan2-test", "--archetype=metacluster",
                   "--domain=unittest", "--building=ut", "--domain=unittest",
                   "--comments=vulcan_localdisk_test"]
        self.noouttest(command)

    # INFO: this piece of code is needed to make autopg logic work for vulcan
    # localdisk, too.
    # TODO we may want to use the actual vulcal local disk cluster personality,
    # it removes the clusterreg part.
    def test_010_addutlccl1(self):
        command = ["add_esx_cluster", "--cluster=%s" % self.cluster,
                   "--metacluster=%s" % self.metacluster, "--room=utroom1",
                   "--buildstatus=build",
                   "--domain=unittest", "--down_hosts_threshold=0",
                   "--archetype=esx_cluster",
                   "--personality=vulcan-local-disk"]
        self.noouttest(command)

    # reusing vulcan2 subnets here.
    def test_020_addutpgsw(self):
        ip = self.net.unknown[17].usable[0]

        self.dsdb_expect_add(self.switch, ip, "xge49",
                             ip.mac)
        command = ["add", "switch", "--switch", self.switch, "--rack", "ut12",
                   "--model", "rs g8000", "--interface", "xge49",
                   "--type", "tor", "--mac", ip.mac, "--ip", ip]
        (out, err) = self.successtest(command)
        self.dsdb_verify()

    # see fakevlan2net
    def test_025_pollutpgsw(self):

        command = ["poll", "switch", "--vlan", "--switch",
                   self.switch]
        (out, err) = self.successtest(command)

        service = self.config.get("broker", "poll_helper_service")
        self.matchoutput(err,
                         "Using jump host nyaqd1.ms.com from service "
                         "instance %s/unittest to run CheckNet "
                         "for switch %s" % (service, self.switch),
                         command)

        # For Nexus switches we have if names, not snmp ids.
        command = "show switch --switch %s" % self.switch
        out = self.commandtest(command.split(" "))

        macs = ["02:02:04:02:12:06", "02:02:04:02:12:07"]
        for i in range(0,2):
            self.matchoutput(out, "Port et1-%d: %s" % (i + 1, macs[i]), command)

    def test_030_addswitch(self):
        self.successtest(["update_esx_cluster", "--cluster=%s" % self.cluster,
                          "--switch=%s" % self.switch])

    def test_050_add_vmhost(self):
        self.noouttest(["add", "machine", "--machine", self.machine,
                        "--rack", "ut3", "--model", "vb1205xm"])

        self.noouttest(["add", "interface", "--interface", "eth0",
                        "--machine", self.machine,
                        "--mac", self.getip().mac])

        self.dsdb_expect_add(self.vmhost, self.getip(), "eth0", self.getip().mac)
        command = ["add", "host", "--hostname", self.vmhost, "--ip", self.getip(),
                   "--machine", self.machine,
                   "--domain", "unittest", "--buildstatus", "build",
                   "--osname", "esxi", "--osversion", "4.0.0",
                   "--archetype", "vmhost",
                   "--personality", "vulcan-local-disk"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_060_bind_host_to_cluster(self):
        self.successtest(["make", "cluster", "--cluster", self.cluster])

        self.successtest(["cluster",
                          "--hostname", self.vmhost, "--cluster", self.cluster])

    def test_065_add_vms(self):
        for i in range(0, 3):
            machine = "utpgm%d" % i

            command = ["add", "machine", "--machine", machine,
                            "--vmhost", self.vmhost, "--model", "utmedium"]
            self.noouttest(command)

    def test_120_cat_vmhost(self):
        command = ["cat", "--hostname=%s" % self.vmhost, "--generate", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out, "template hostdata/%s;" % self.vmhost,
                         command)
        self.matchoutput(out,
                         '"system/resources/virtual_machine" '
                         '= append(create("resource/host/%s/'
                         'virtual_machine/utpgm0/config"));' % self.vmhost,
                         command)


    def test_122_addvmfswohost(self):
        # Try to bind to fs1 of another host.
        command = ["add", "disk", "--machine", "utpgm0",
            "--disk", "sda", "--controller", "scsi",
            "--filesystem", "utfs1n", "--address", "0:0",
            "--size", "34"]

        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Not Found: Filesystem utfs1n, hostresource instance not found.",
                         command)

    def test_125_addvmfs(self):
        command = ["add_filesystem", "--filesystem=utfs1", "--type=ext3",
                   "--mountpoint=/mnt", "--blockdevice=/dev/foo/bar",
                   "--bootmount",
                   "--dumpfreq=1", "--fsckpass=3", "--options=ro",
                   "--comments=testing",
                   "--hostname=%s" % self.vmhost]
        self.successtest(command)

        # Quick test
        command = ["cat", "--filesystem=utfs1",
                   "--hostname=%s" % self.vmhost]
        out = self.commandtest(command)
        self.matchoutput(out, '"name" = "utfs1";', command)

    def test_130_addutpgm0disk(self):
        for i in range(0, 3):
            machine = "utpgm%d" % i
            self.noouttest(["add", "disk", "--machine", machine,
                "--disk", "sda", "--controller", "scsi",
                "--filesystem", "utfs1", "--address", "0:0",
                "--size", "34"])

    def test_140_verifyaddutpgm0disk(self):
        for i in range(0, 3):
            machine = "utpgm%d" % i

            command = ["show", "machine", "--machine", machine]
            out = self.commandtest(command)

            self.searchoutput(out, r"Disk: sda 34 GB scsi \(virtual_localdisk from utfs1\) \[boot\]$",
                              command)

    def test_160_addinterfaces(self):
        # TODO: fixed mac addresses grabbed from test_vulcan2 until automac\pg
        # for localdisk is implemented.

        # Pick first one with automac(fakebind data should be fixed)
        for i in range(0, 2):
            self.noouttest(["add", "interface", "--machine", "utpgm%d" % i,
                            "--interface", "eth0", "--automac", "--autopg"])

    def test_150_verifyutfs1(self):
        command = ["show_filesystem", "--filesystem=utfs1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Filesystem: utfs1", command)
        self.matchoutput(out, "Bound to: Host %s" % self.vmhost, command)
        self.matchoutput(out, "Disk Count: 3", command)

    def test_200_make_host(self):
        command = ["make", "--hostname", "utpgh0.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "sent 1 server notifications", command)

        command = ["show", "host", "--hostname", "utpgh0.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "Template: service/vcenter/ut", command)


    def check_path_exclusive(self, path, wrongpath):
        self.failIf(os.path.exists(wrongpath),
                    "Plenary file '%s' not removed." % wrongpath)
        self.failUnless(os.path.exists(path),
                        "Plenary file '%s' not created." % path)

    def test_210_move_machine(self):
        # self.plenary_core = "machine/%(hub)s/%(building)s/%(rack)s" % self.__dict__
        oldpath = self.plenary_name("machine", "americas", "ut", "ut3", self.machine)
        newpath = self.plenary_name("machine", "americas", "ut", "ut13", self.machine)

        self.check_path_exclusive(oldpath, newpath)
        self.noouttest(["update", "machine", "--machine", self.machine,
                        "--rack", "ut13"])
        self.check_path_exclusive(newpath, oldpath)

    def test_220_check_location(self):
        command = ["show", "machine", "--machine", self.machine]
        out = self.commandtest(command)
        self.matchoutput(out, "Rack: ut13", command)

    def test_230_check_vm_location(self):
        for i in range(0, 3):
            machine = "utpgm%d" % i
            command = ["show", "machine", "--machine", machine]
            out = self.commandtest(command)
            self.matchoutput(out, "Rack: ut13", command)


    # deletes


    def test_290_delutpgm0disk(self):
        for i in range(0, 3):
            self.noouttest(["del", "disk", "--machine", "utpgm%d" % i,
                "--controller", "scsi", "--disk", "sda"])

    # deleting fs before depending disk would drop them as well
    def test_295_delvmfs(self):
        command = ["del_filesystem", "--filesystem=utfs1",
                   "--hostname=%s" % self.vmhost]
        self.successtest(command)

    def test_310_del_vms(self):
        for i in range(0, 3):
            machine = "utpgm%d" % i

            self.noouttest(["del", "machine", "--machine", machine])

    def test_320_del_vmhost(self):

        self.dsdb_expect_delete(self.getip())
        command = ["del", "host", "--hostname", self.vmhost]
        err = self.statustest(command)
        self.matchoutput(err, "sent 1 server notifications", command)
        self.dsdb_verify()

        self.noouttest(["del", "machine", "--machine", self.machine])

    def test_308_delutpgsw(self):
        ip = self.net.unknown[17].usable[0]
        plenary = self.plenary_name("switchdata", self.switch)
        self.failUnless(os.path.exists(plenary),
                    "Plenary file '%s' does not exist" % plenary)

        self.dsdb_expect_delete(ip)
        command = "del switch --switch %s" % self.switch
        self.noouttest(command.split(" "))

        self.failIf(os.path.exists(plenary),
                    "Plenary file '%s' still exists" % plenary)

        self.dsdb_verify()

    def test_330_delutlccl1(self):
        command = ["del_esx_cluster", "--cluster=%s" % self.cluster]
        self.successtest(command)

    def test_340_delutmc9(self):
        command = ["del_metacluster", "--metacluster=%s" % self.metacluster]
        err = self.statustest(command)
        self.matchoutput(err, "sent 1 server notifications", command)

        self.assertFalse(os.path.exists(os.path.join(
            self.config.get("broker", "profilesdir"), "clusters",
            self.metacluster + self.profile_suffix)))

    def test_500_del_vlocal(self):
        command = ["del_personality", "--archetype", "esx_cluster",
                   "--personality", "vulcan-local-disk"]
        self.noouttest(command)

        command = ["unmap", "service", "--service", "esx_management_server", "--instance", "ut.a",
                   "--building", "ut", "--personality", "vulcan-local-disk",
                   "--archetype", "vmhost"]
        self.noouttest(command)

        command = ["del_required_service", "--service", "esx_management_server",
                   "--personality", "vulcan-local-disk",
                   "--archetype", "vmhost"]
        self.noouttest(command)

        command = ["del_personality", "--archetype", "vmhost",
                   "--personality", "vulcan-local-disk"]
        self.noouttest(command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestVulcanLocalDisk)
    unittest.TextTestRunner(verbosity=2).run(suite)
