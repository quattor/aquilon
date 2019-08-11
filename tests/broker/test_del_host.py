#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008-2019  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Module for testing the del host command."""

from datetime import datetime

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand
from notificationtest import VerifyNotificationsMixin
from machinetest import MachineTestMixin
from utils import MockHub


class TestDelHost(VerifyNotificationsMixin, MachineTestMixin,
                  TestBrokerCommand):

    def to_windows(self, hostname):
        # Aquilon-6292 makes it impossible to delete 'aquilon' hosts in
        # protected states.  A simple workaround to make legacy tests work
        # again is to make them windows hosts.
        # The real tests for del_host in all status and for any archetype are
        # in test_200_* below, and in unit tests for CommandDelHost.
        self.successtest(
            ['reconfigure', '--hostname', hostname,
             '--archetype', 'windows',
             '--personality', 'generic',
             '--osname', 'windows',
             '--osversion', 'generic'])

    def test_100_del_unittest02(self):
        self.dsdb_expect_delete(self.net['unknown0'].usable[11])
        host = 'unittest02.one-nyp.ms.com'
        self.to_windows(host)
        command = ['del_host', '--hostname', host]
        self.statustest(command)
        self.dsdb_verify()
        self.verify_buildfiles('unittest', host,
                               want_exist=False, command='del_host')

    def test_105_verify_del_unittest02(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        self.notfoundtest(command.split(" "))

    def test_105_verify_service_plenary(self):
        command = ["cat", "--service", "utsvc", "--instance", "utsi2",
                   "--server"]
        out = self.commandtest(command)
        self.matchclean(out, "unittest02", command)

    def test_110_del_unittest00(self):
        self.dsdb_expect_delete(self.net["unknown0"].usable[2])
        command = "del host --hostname unittest00.one-nyp.ms.com"
        self.statustest(command.split(" "))
        self.dsdb_verify()

    def test_115_verify_del_unittest00(self):
        command = "show host --hostname unittest00.one-nyp.ms.com"
        self.notfoundtest(command.split(" "))

    def test_115_verify_del_unittest00_dns(self):
        command = "show address --fqdn unittest00.one-nyp.ms.com"
        self.notfoundtest(command.split(" "))

    def test_115_verify_ut3c1n3(self):
        command = "show machine --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        # The primary name must be gone
        self.matchclean(out, "Primary Name:", command)
        self.matchclean(out, "unittest00.one-nyp.ms.com", command)
        # No interface should have the IP address
        self.matchclean(out, "Auxiliary:", command)
        self.matchclean(out, "Provides:", command)
        self.matchclean(out, str(self.net["unknown0"].usable[2]), command)

    # unittest01.one-nyp.ms.com gets deleted in test_del_windows_host.

    def test_120_del_aurora_with_node(self):
        command = ["del_host", "--hostname", "{}.ms.com".format(self.aurora_with_node)] + self.valid_just_tcm
        err = self.statustest(command)
        self.matchoutput(err,
                         "WARNING: removing host %s.ms.com from AQDB "
                         "and *not* changing DSDB." % self.aurora_with_node,
                         command)

    def test_121_verify_del_aurora_with_node(self):
        command = "show host --hostname %s.ms.com" % self.aurora_with_node
        self.notfoundtest(command.split(" "))

    def test_125_del_aurora_without_node(self):
        command = ["del_host", "--hostname", "{}.ms.com".format(self.aurora_without_node)] + self.valid_just_tcm
        err = self.statustest(command)
        self.matchoutput(err,
                         "WARNING: removing host %s.ms.com from AQDB "
                         "and *not* changing DSDB." % self.aurora_without_node,
                         command)

    def test_126_verify_del_aurora_without_node(self):
        command = "show host --hostname %s.ms.com" % self.aurora_without_node
        self.notfoundtest(command.split(" "))

    def test_140_del_nyaqd1(self):
        command = ["del_host", "--hostname", "nyaqd1.ms.com"] + self.valid_just_tcm
        self.statustest(command)

    def test_140_verify_del_nyaqd1(self):
        command = "show host --hostname nyaqd1.ms.com"
        self.notfoundtest(command.split(" "))

    def test_150_del_aurora_default_os(self):
        command = "del host --hostname test-aurora-default-os.ms.com --quiet"
        self.noouttest(command.split(" "))
        self.dsdb_verify(empty=True)

    def test_151_verify_del_aurora_default_os(self):
        command = "show host --hostname test-aurora-default-os.ms.com"
        self.notfoundtest(command.split(" "))

    def test_155_del_windows_default_os(self):
        ip = self.net["tor_net_0"].usable[5]
        self.dsdb_expect_delete(ip)
        command = "del host --hostname test-windows-default-os.msad.ms.com --quiet"
        self.noouttest(command.split(" "))
        self.dsdb_verify()

    def test_156_verify_del_windows_default_os(self):
        command = "show host --hostname test-windows-default-os.msad.ms.com"
        self.notfoundtest(command.split(" "))

    def test_160_del_jack(self):
        ip = self.net["tor_net_0"].usable[9]
        self.dsdb_expect_delete(ip)
        command = "del host --hostname jack.cards.example.com"
        self.statustest(command.split(" "))
        self.dsdb_verify()

    def test_165_verify_del_jack(self):
        command = "show host --hostname jack.cards.example.ms.com"
        self.notfoundtest(command.split(" "))

    def test_170_unbind_notify(self):
        hostname = self.config.get("unittest", "hostname")
        command = ["unbind", "server", "--service", "utnotify",
                   "--instance", "localhost", "--hostname", hostname]
        err = self.statustest(command)
        self.matchoutput(err,
                         "Warning: Host %s is missing the following required "
                         "services" % hostname,
                         command)

    def test_171_del_notify(self):
        hostname = self.config.get("unittest", "hostname")
        self.to_windows(hostname)
        self.dsdb_expect_delete("127.0.0.1")
        basetime = datetime.now()
        command = ["del", "host", "--hostname", hostname]
        self.statustest(command)
        self.wait_notification(basetime, 0)
        self.dsdb_verify()

    def test_200_allowed_by_default_for_selected_states(self):
        # It should be only allowed for states specified in
        # CommandDelHost._default_allowed_states: blind, build, decommissioned,
        # failed, and install.
        allowed = {'blind', 'build', 'decommissioned', 'failed', 'install'}
        mh = MockHub(self)
        # Ensure that the archetype defined by MockHub does not have a
        # corresponding 'archetype_xxx' config section, and thus does not
        # override the defaults.
        assert ('archetype_{}'.format(mh.default_archetype)
                not in self.config.sections())
        for status in allowed:
            host = mh.add_host(extra_arguments=['--buildstatus', status])
            machine = mh.hosts[host]['machine']
            net = mh.networks[mh.machines[machine]['network']]['net']
            ip = net.usable[mh.machines[machine]['net_index']]
            self.dsdb_expect_delete(ip=ip)
            self.successtest(['del_host', '--hostname', host])
            self.dsdb_verify()
            del mh.hosts[host]
            self.notfoundtest(['show_host', '--hostname', host])
        mh.delete()

    def test_200_forbidden_by_default_for_selected_states(self):
        # It should be only allowed for states specified in
        # CommandDelHost._default_allowed_states, and thus forbidden in
        # states: almostready, ready, rebuild, and reinstall.
        protected = {'almostready', 'ready', 'rebuild', 'reinstall'}
        allowed = {'blind', 'build', 'decommissioned', 'failed', 'install'}
        mh = MockHub(self)
        # Ensure that the archetype defined by MockHub does not have a
        # corresponding 'archetype_xxx' config section, and thus does not
        # override the defaults.
        assert ('archetype_{}'.format(mh.default_archetype)
                not in self.config.sections())
        for status in protected:
            host = mh.add_host(extra_arguments=['--buildstatus', status])
            command = ['del_host', '--hostname', host]
            err = self.badrequesttest(command)
            self.matchoutput(err,
                             'host status "{}" combined with'.format(status),
                             command)
            self.matchoutput(err, 'archetype configuration',
                             command)
            self.matchoutput(err, ' prevents it from being deleted',
                             command)
            self.matchoutput(err, 'case of archetype "{}"'.format(
                mh.default_archetype), command)
            self.matchoutput(err, 'only hosts with the following status '
                                  'can be deleted',
                             command)
            self.matchoutput(err, ': {}'.format(', '.join(sorted(allowed))),
                             command)
        mh.delete()

    def test_300_del_afsbynet(self):
        self.delete_host("afs-by-net.aqd-unittest.ms.com",
                         self.net["netsvcmap"].usable[0], "ut3c5n11")

    def test_300_del_netmappers(self):
        self.delete_host("netmap-pers.aqd-unittest.ms.com",
                         self.net["netperssvcmap"].usable[0], "ut3c5n12")

    def test_300_del_unittest12(self):
        self.delete_host("unittest12.aqd-unittest.ms.com",
                         self.net["unknown0"].usable[7], "ut3s01p1")

    def test_300_del_unittest15(self):
        self.delete_host("unittest15.aqd-unittest.ms.com",
                         self.net["tor_net_0"].usable[1], "ut8s02p1")

    def test_300_del_unittest16(self):
        self.delete_host("unittest16.aqd-unittest.ms.com",
                         self.net["tor_net_0"].usable[2], "ut8s02p2")

    def test_300_del_unittest17(self):
        self.delete_host("unittest17.aqd-unittest.ms.com",
                         self.net["tor_net_0"].usable[3], "ut8s02p3",
                         manager_ip=self.net["ut8_oob"].usable[3])

    def test_300_del_unittest18(self):
        self.delete_host("unittest18.aqd-unittest.ms.com",
                         self.net["unknown0"].usable[18], "ut3c1n8")

    def test_300_del_unittest20(self):
        host = 'unittest20.aqd-unittest.ms.com'
        self.to_windows(host)
        # The transits are deleted in test_del_interface_address
        self.delete_host(host, self.net['zebra_vip'].usable[2], 'ut3c5n2')

    def test_300_del_unittest21(self):
        self.delete_host("unittest21.aqd-unittest.ms.com",
                         self.net["zebra_eth0"].usable[1], "ut3c5n3")

    def test_300_del_unittest22(self):
        self.delete_host("unittest22.aqd-unittest.ms.com",
                         self.net["zebra_eth0"].usable[2], "ut3c5n4")

    def test_300_del_unittest23(self):
        self.delete_host("unittest23.aqd-unittest.ms.com",
                         self.net["vpls"].usable[1], "ut3c5n5")

    def test_300_del_unittest24(self):
        self.check_plenary_exists("machine", "americas", "np", "np3", "np3c5n5")
        self.delete_host("unittest24.one-nyp.ms.com",
                         self.net["vpls"].usable[2], "np3c5n5")
        self.check_plenary_gone("machine", "americas", "np", "np3", "np3c5n5")

    def test_300_del_unittest25(self):
        self.delete_host("unittest25.aqd-unittest.ms.com",
                         self.net["unknown0"].usable[20], "ut3c5n7")

    def test_300_del_unittest26(self):
        host = 'unittest26.aqd-unittest.ms.com'
        self.to_windows(host)
        self.delete_host(host, self.net['unknown0'].usable[23], 'ut3c5n8')

    def test_300_del_filer(self):
        self.delete_host("filer1.ms.com", self.net["vm_storage_net"].usable[25],
                         "filer1")

    def test_300_del_f5test(self):
        self.delete_host("f5test.aqd-unittest.ms.com", self.net["f5test"].ip,
                         "f5test")

    def test_300_del_utinfra1(self):
        eth0_ip = self.net["unknown0"].usable[33]
        eth1_ip = self.net["unknown1"].usable[34]
        ip = self.net["zebra_vip"].usable[0]
        self.delete_host("infra1.aqd-unittest.ms.com", ip, "ut3c5n13",
                         eth0_ip=eth0_ip, eth1_ip=eth1_ip)

    def test_300_del_utinfra2(self):
        eth0_ip = self.net["unknown0"].usable[38]
        eth1_ip = self.net["unknown1"].usable[37]
        ip = self.net["zebra_vip"].usable[1]
        self.delete_host("infra2.aqd-unittest.ms.com", ip, "ut3c5n14",
                         eth0_ip=eth0_ip, eth1_ip=eth1_ip)

    def test_300_del_npinfra1(self):
        eth0_ip = self.net["unknown0"].usable[35]
        eth1_ip = self.net["unknown1"].usable[36]
        ip = self.net["zebra_vip2"].usable[0]
        self.delete_host("infra1.one-nyp.ms.com", ip, "np3c5n13",
                         eth0_ip=eth0_ip, eth1_ip=eth1_ip)

    def test_300_del_npinfra2(self):
        eth0_ip = self.net["unknown0"].usable[43]
        eth1_ip = self.net["unknown1"].usable[39]
        ip = self.net["zebra_vip2"].usable[1]
        self.delete_host("infra2.one-nyp.ms.com", ip, "np3c5n14",
                         eth0_ip=eth0_ip, eth1_ip=eth1_ip)

    def test_300_del_hp_rack_hosts(self):
        servers = 0
        net = self.net["hp_eth0"]
        mgmt_net = self.net["hp_mgmt"]
        for i in range(51, 100):
            port = i - 50
            if servers < 10:
                servers += 1
                hostname = "server%d.aqd-unittest.ms.com" % servers
            else:
                hostname = "aquilon%d.aqd-unittest.ms.com" % i
            machine = "ut9s03p%d" % port
            ip = net.usable[port]
            if hostname == 'aquilon67.aqd-unittest.ms.com':
                ip = self.net["ut_bucket2_localvip"].usable[0]
            self.to_windows(hostname)
            self.delete_host(hostname, ip, machine,
                             manager_ip=mgmt_net.usable[port],
                             justification=True)

    def test_300_del_ut10_hosts(self):
        net = self.net["ut10_eth0"]
        mgmt_net = self.net["ut10_oob"]
        for i in range(101, 111):
            port = i - 100
            hostname = "evh%d.aqd-unittest.ms.com" % port
            machine = "ut10s04p%d" % port
            self.delete_host(hostname, net.usable[port], machine,
                             manager_ip=mgmt_net.usable[port])

    def test_300_del_10gig_rack_hosts(self):
        net = self.net["vmotion_net"]
        for i in range(1, 25):
            hostname = "evh%d.aqd-unittest.ms.com" % (i + 50)
            if i < 13:
                port = i
                machine = "ut11s01p%d" % i
                mgmt_net = self.net["ut11_oob"]
            else:
                port = i - 12
                machine = "ut12s02p%d" % (i - 12)
                mgmt_net = self.net["ut12_oob"]
            self.delete_host(hostname, net.usable[i + 1], machine,
                             manager_ip=mgmt_net[port])

    def test_300_del_utmc8_hosts(self):
        self.delete_host("evh80.aqd-unittest.ms.com",
                         self.net["ut14_net"].usable[0], "ut14s1p0",
                         eth1_ip=self.net["vm_storage_net"].usable[26],
                         manager_ip=self.net["ut14_oob"].usable[0])
        self.delete_host("evh81.aqd-unittest.ms.com",
                         self.net["ut14_net"].usable[1], "ut14s1p1",
                         eth1_ip=self.net["vm_storage_net"].usable[27],
                         manager_ip=self.net["ut14_oob"].usable[1])

    def test_300_del_utmc9_hosts(self):
        self.delete_host("evh82.aqd-unittest.ms.com",
                         self.net["ut14_net"].usable[2], "ut14s1p2",
                         manager_ip=self.net["ut14_oob"].usable[2])
        self.delete_host("evh83.aqd-unittest.ms.com",
                         self.net["ut14_net"].usable[3], "ut14s1p3",
                         manager_ip=self.net["ut14_oob"].usable[3])

    def test_310_del_network_device(self):
        command = ["del", "host", "--hostname", "ut3gd1r04.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Command del_host should only be used for machines, "
                              "but ut3gd1r04.aqd-unittest.ms.com is a switch.",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelHost)
    unittest.TextTestRunner(verbosity=2).run(suite)
