#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015,2016,2017  Contributor
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
"""Module for testing to setup network devices"""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from six import iteritems

from brokertest import TestBrokerCommand

# This test case sets up a network that look like the following:
#
# +---> netuc_netmgmt_1a                               netuc_netmgmt_1b <---+
# |      (4.1.0.0/26)                                   (4.1.0.64/26)       |
# |                                                                         |
# |            +---> netuc_transit_1a <=> netuc_transit_1b <---+            |
# |            |      (4.1.1.0/26)         (4.1.2.0/26)        |            |
# |            |        (vlan101)            (vlan201)         |            |
# |            |                                               |            |
# + np01fdlr01 +---> netuc_transit_2a <=> netuc_transit_2b <---+ np01fdlr03 +
# |            |      (4.1.1.64/26)        (4.1.2.64/26)       |            |
# |            |        (vlan102)            (vlan202)         |            |
# |            |                                               |            |
# + np01fdlr02 +---> netuc_transit_3a <=> netuc_transit_3b <---+ np01fdlr04 +
#              |      (4.1.1.128/26)       (4.1.2.128/26)      |
#              |        (vlan103)            (vlan203)         |
#              |                                               |
#              +---> netuc_transit_4a <=> netuc_transit_4b <---+
#                     (4.1.1.192/26)       (4.1.2.192/26)
#                       (vlan104)            (vlan204)
#
# - Sides:
#   There are two sides in the above diagream.  The idea is that each side
#   is serviced by a pair of independent routers.  The result is that hosts
#   can connect to two resiliant transit subnets (see the <=> on the diagram).
#
# - Routers
#   There are for routers in total (np01fdlr01-04), two on side 'a' and two
#   on side 'b'.
#
# - Management networks:
#   Each side has a 'virtual' management network which is used by the router
#   loopback addresses.  So np01fdlr01/02 use the 'a' side management
#   network netuc_netmgmt_1a.
#
# - Transit networks:
#   There are eight transit networks, four on each side.  Each belong to the
#   routers on either side.  Each router has a vlan interface on these,
#   where the lowest numberd router takes the lowest numbered address.
#
# - Shared addresss:
#   An HSRP address is shared by the 01/02 and 03/04 router paris, where
#   an odd numberd router (i.e 03) is the primary for an odd numbered
#   network (netuc_transit_1b) - and visa versa for even numbered routers.
#
config = {
    'domain': 'net.ms.com',
    'gateways': {
        'netuc_transit_1a': [('np01fdlr01', 'vlan101'), ('np01fdlr02', 'vlan101')],
        'netuc_transit_2a': [('np01fdlr02', 'vlan102'), ('np01fdlr01', 'vlan102')],
        'netuc_transit_3a': [('np01fdlr01', 'vlan103'), ('np01fdlr02', 'vlan103')],
        'netuc_transit_4a': [('np01fdlr02', 'vlan104'), ('np01fdlr01', 'vlan104')],
        'netuc_transit_1b': [('np01fdlr03', 'vlan201'), ('np01fdlr04', 'vlan201')],
        'netuc_transit_2b': [('np01fdlr04', 'vlan202'), ('np01fdlr03', 'vlan202')],
        'netuc_transit_3b': [('np01fdlr03', 'vlan203'), ('np01fdlr04', 'vlan203')],
        'netuc_transit_4b': [('np01fdlr04', 'vlan204'), ('np01fdlr03', 'vlan204')],
    },
    'devices': {
        'np01fdlr01': {
            'model': 'cat6509',
            'mgmt_interface': 'lo0',
            'interfaces': {
                'lo0': {
                    'net': 'netuc_netmgmt_1a',
                    'ipidx': 1,
                },
                'vlan101': {
                    'net': 'netuc_transit_1a',
                    'ipidx': 2,
                },
                'vlan102': {
                    'net': 'netuc_transit_2a',
                    'ipidx': 2,
                },
                'vlan103': {
                    'net': 'netuc_transit_3a',
                    'ipidx': 2,
                },
                'vlan104': {
                    'net': 'netuc_transit_4a',
                    'ipidx': 2,
                }
            }
        },
        'np01fdlr02': {
            'model': 'cat6509',
            'mgmt_interface': 'lo0',
            'interfaces': {
                'lo0': {
                    'net': 'netuc_netmgmt_1a',
                    'ipidx': 2,
                },
                'vlan101': {
                    'net': 'netuc_transit_1a',
                    'ipidx': 3,
                },
                'vlan102': {
                    'net': 'netuc_transit_2a',
                    'ipidx': 3,
                },
                'vlan103': {
                    'net': 'netuc_transit_3a',
                    'ipidx': 3,
                },
                'vlan104': {
                    'net': 'netuc_transit_4a',
                    'ipidx': 3,
                }
            }
        },
        'np01fdlr03': {
            'model': 'cat6509',
            'mgmt_interface': 'lo0',
            'interfaces': {
                'lo0': {
                    'net': 'netuc_netmgmt_1b',
                    'ipidx': 1,
                },
                'vlan201': {
                    'net': 'netuc_transit_1b',
                    'ipidx': 2,
                },
                'vlan202': {
                    'net': 'netuc_transit_2b',
                    'ipidx': 2,
                },
                'vlan203': {
                    'net': 'netuc_transit_3b',
                    'ipidx': 2,
                },
                'vlan204': {
                    'net': 'netuc_transit_4b',
                    'ipidx': 2,
                }
            }
        },
        'np01fdlr04': {
            'model': 'cat6509',
            'mgmt_interface': 'lo0',
            'interfaces': {
                'lo0': {
                    'net': 'netuc_netmgmt_1b',
                    'ipidx': 2,
                },
                'vlan201': {
                    'net': 'netuc_transit_1b',
                    'ipidx': 3,
                },
                'vlan202': {
                    'net': 'netuc_transit_2b',
                    'ipidx': 3,
                },
                'vlan203': {
                    'net': 'netuc_transit_3b',
                    'ipidx': 3,
                },
                'vlan204': {
                    'net': 'netuc_transit_4b',
                    'ipidx': 3,
                }
            }
        }
    }
}

# When running these unit test on their own the following flags will
# help skip some parts of the test that are not generally needed in
# personal development enviornments
#flags = ('skip_prereq', 'skip_dsdb', 'skip_add')
#flags = ('skip_prereq', 'skip_dsdb', 'skip_delete')
#flags = ('skip_prereq', 'skip_dsdb')
flags = ()


class TestUsecaseNetworks(TestBrokerCommand):

    ########## SETUP STAGE ##########

    def test_100_add_dns_domain(self):
        if 'skip_prereq' in flags:
            return True
        self.dsdb_expect("add_dns_domain -domain_name %s -comments " % config['domain'])
        self.noouttest(["add", "dns_domain",
                        "--dns_domain", config['domain']] + self.valid_just_tcm)
        self.dsdb_verify()

    def test_100_add_6509_model(self):
        if 'skip_prereq' in flags:
            return True
        self.noouttest(["add_model", "--model", "cat6509",
                        "--vendor", "cisco", "--type=switch-router"])

    ########## ADDITION STAGE ##########

    def test_200_add_networks(self):
        if 'skip_add' in flags:
            return True
        for network in self.net:
            if not network.name.startswith('netuc_'):
                continue

            command = ["add_network", "--network=%s" % network.name,
                       "--ip=%s" % network.ip,
                       "--netmask=%s" % network.netmask,
                       "--" + network.loc_type, network.loc_name,
                       "--type=%s" % network.nettype,
                       "--side=%s" % network.side]
            if network.comments:
                command.extend(["--comments", network.comments])
            self.noouttest(command)
            self.check_plenary_exists('network', 'internal', str(network.ip), 'config')

    def test_201_add_routers(self):
        if 'skip_add' in flags:
            return True
        for (name, dev_attrs) in iteritems(config['devices']):
            fqdn = name + '.' + config['domain']
            interface = dev_attrs['mgmt_interface']
            if_attrs = dev_attrs['interfaces'][interface]
            net = self.net[if_attrs['net']]
            ip = net[if_attrs['ipidx']]
            iftype = if_attrs['type'] if 'type' in if_attrs else 'loopback'
            self.dsdb_expect_add(fqdn, ip, interface)
            self.successtest(["add", "network_device", "--type", "misc",
                              "--network_device", fqdn,
                              "--ip", ip, "--interface", interface,
                              "--iftype", iftype,
                              "--%s" % net.loc_type, net.loc_name,
                              "--model", dev_attrs['model']])
            if 'skip_dsdb' not in flags:
                self.dsdb_verify()

    def test_202_add_interfaces(self):
        if 'skip_add' in flags:
            return True
        for (dev_name, dev_attrs) in iteritems(config['devices']):
            fqdn = dev_name + '.' + config['domain']
            for (if_name, if_attrs) in iteritems(dev_attrs['interfaces']):
                if if_name == dev_attrs['mgmt_interface']:
                    continue
                iftype = if_attrs['type'] if 'type' in if_attrs else "virtual"
                command = ["add", "interface", "--interface", if_name,
                           "--iftype", iftype,
                           "--network_device", fqdn]
                self.noouttest(command)

    def test_203_add_addresses(self):
        if 'skip_add' in flags:
            return True
        for (dev_name, dev_attrs) in iteritems(config['devices']):
            fqdn = dev_name + '.' + config['domain']
            for (if_name, if_attrs) in iteritems(dev_attrs['interfaces']):
                if if_name == dev_attrs['mgmt_interface']:
                    continue
                net = self.net[if_attrs['net']]
                ip = net[if_attrs['ipidx']]
                if_fqdn = dev_name + '-' + if_name + '.' + config['domain']
                self.dsdb_expect_add(if_fqdn, ip, if_name, primary=fqdn)
                command = ["add", "interface", "address",
                           "--network_device", fqdn,
                           "--interface", if_name, "--ip", ip]
                self.noouttest(command)
                if 'skip_dsdb' not in flags:
                    self.dsdb_verify()

    def test_204_add_hsrp(self):
        if 'skip_add' in flags:
            return True
        for net_name, gateways in iteritems(config['gateways']):
            net = self.net[net_name]
            ip = net[1] # Always use first address
            gw_fqdn = '-'.join(net.name.split('_')[1:] + ['gateway']) + '.' + config['domain']
            priority = 100
            for (dev_name, if_name) in gateways:
                fqdn = dev_name + '.' + config['domain']
                # Note, this only happens the first time an address is added
                if priority == 100:
                    self.dsdb_expect_add(gw_fqdn, ip)
                # We only specify the FQDN when creating the first interface
                command = ["add", "interface", "address",
                           "--network_device", fqdn,
                           "--interface", if_name, "--label", "hsrp",
                           "--fqdn", gw_fqdn, "--ip", ip,
                           "--shared", "--priority", priority]
                self.noouttest(command)
                if 'skip_dsdb' not in flags and priority == 100:
                    self.dsdb_verify()
                priority = priority + 1

    def test_205_add_default_route(self):
        if 'skip_add' in flags:
            return True

        net_list = [net for net in self.net if (net.name.startswith('netuc_') and net.nettype != 'management')]

        for network in net_list[:5]:
            fqdn = '-'.join(network.name.split('_')[1:] + ['gateway']) + '.' + config['domain']
            command = ["add_router_address", "--fqdn", fqdn]
            self.noouttest(command)

        for network in net_list[5:10]:
            command = ["add_router_address", "--ip", network[1]]
            self.noouttest(command)

        for network in net_list[10:]:
            fqdn = '-'.join(network.name.split('_')[1:] + ['gateway']) + '.' + config['domain']
            command = ["add_router_address", "--fqdn", fqdn, "--ip", network[1]]
            self.noouttest(command)

    ########## TESTING STAGE ##########

    def test_301_network_plenary(self):
        for (net_name, net_attrs) in iteritems(config['gateways']):
            net = self.net[net_name]

            pri_router = net_attrs[0][0]
            pri_router_fqdn = pri_router + '.' + config['domain']
            pri_router_if = net_attrs[0][1]
            _pri_router_ip = config['devices'][pri_router]['interfaces'][pri_router_if]
            pri_router_ip = self.net[_pri_router_ip['net']][_pri_router_ip['ipidx']]

            sec_router = net_attrs[1][0]
            sec_router_fqdn = sec_router + '.' + config['domain']
            sec_router_if = net_attrs[1][1]
            _sec_router_ip = config['devices'][sec_router]['interfaces'][sec_router_if]
            sec_router_ip = self.net[_sec_router_ip['net']][_sec_router_ip['ipidx']]

            command = ["cat", "--networkip", str(net.ip)]
            out = self.commandtest(command)

            m = lambda x: self.matchoutput(out, x, command)
            m('structure template network/internal/%s/config' % net.ip)
            m('"name" = "%s"' % net.name)
            m('"network" = "%s"' % net.ip)
            m('"netmask" = "%s"' % net.netmask)
            m('"broadcast" = "%s"' % net.broadcast_address)
            m('"prefix_length" = %d' % net.prefixlen)
            m('"type" = "%s"' % net.nettype)
            m('"side" = "%s"' % net.side)
            m('"sysloc/building" = "%s"' % net.loc_name)
            m('"network_environment/name" = "internal"')

            s = lambda x: self.searchoutput(out, x, command)
            assignment = lambda lhs, rhs: r'"%s"\s*=\s*%s' % (lhs, rhs)
            nlisti = lambda i: r'"%s",\s*"%s"\s*' % (i[0], i[1])
            nlist = lambda *l: r'nlist\(\s*' + r',\s*'.join(map(nlisti, l)) + r'\)\s*'
            slist = lambda *l: r'list\(\s*' + r',\s*'.join(l) + r'\)\s*'
            s(assignment(r'router_address/{%s}/providers' % net[1],
                         slist(nlist(("interface", pri_router_if),
                                     ("ip", pri_router_ip),
                                     ("router", pri_router_fqdn)),
                               nlist(("interface", sec_router_if),
                                     ("ip", sec_router_ip),
                                     ("router", sec_router_fqdn)))))

    def test_305_test_router_address_using_netdev_ip(self):
        net = self.net["tor_net_12"]
        ip = net[1]
        command = ['add_interface', '--iftype', 'virtual', '--interface', 'v700',
                   '--network_device', 'ut3gd1r01.aqd-unittest.ms.com']
        self.noouttest(command)
        self.dsdb_expect_add("ut3gd1r01-v700.aqd-unittest.ms.com", ip,
                             "v700", primary="ut3gd1r01.aqd-unittest.ms.com")
        command = ['add_interface_address', '--interface', 'v700', '--ip',
                   ip, '--network_device', 'ut3gd1r01.aqd-unittest.ms.com']
        out, err = self.successtest(command)
        self.matchoutput(err,
                         "Bunker violation: rack ut3 is inside "
                         "bunker zebrabucket.ut, but network "
                         "tor_net_12 [{}] is not bunkerized.".format(net),
                         command)
        self.dsdb_verify()
        command = ['add_router_address', '--ip', ip]
        self.noouttest(command)

    def test_306_test_router_address_using_netdev_show(self):
        ip = self.net["tor_net_12"][1]
        command = ['show_router_address', '--fqdn', 'ut3gd1r01-v700.aqd-unittest.ms.com']
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Router: ut3gd1r01-v700.aqd-unittest.ms.com [{}]".format(ip),
                         command)
        self.matchoutput(out,
                         "Network: tor_net_12 [4.2.5.0/25]",
                         command)

    def test_307_test_router_address_using_netdev_del(self):
        ip = self.net["tor_net_12"][1]
        self.dsdb_expect_delete(ip)
        command = ['del_interface_address', '--interface', 'v700', '--ip',
                   ip, '--network_device', 'ut3gd1r01.aqd-unittest.ms.com']
        self.noouttest(command)
        self.dsdb_verify()
        command = ['del_interface', '--interface', 'v700', '--network_device', 'ut3gd1r01.aqd-unittest.ms.com']
        self.noouttest(command)

    def test_308_test_router_address_using_netdev_show(self):
        ip = self.net["tor_net_12"][1]
        command = ['show_router_address', '--ip', ip]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Router: unknown [{}]".format(ip),
                         command)
        self.matchoutput(out,
                         "Network: tor_net_12 [4.2.5.0/25]",
                         command)

    ########## DELETEION STAGE ##########

    def test_804_del_default_route(self):
        if 'skip_delete' in flags:
            return True
        for network in self.net:
            if not network.name.startswith('netuc_'):
                continue
            if network.nettype == 'management':
                continue
            fqdn = '-'.join(network.name.split('_')[1:] + ['gateway']) + '.' + config['domain']
            command = ["del_router_address", "--fqdn", fqdn]
            self.noouttest(command)

    def test_805_del_hsrp(self):
        if 'skip_delete' in flags:
            return True
        for net_name, gateways in iteritems(config['gateways']):
            net = self.net[net_name]
            ip = net[1] # Always use first address
            if 'skip_dsdb' not in flags:
                self.dsdb_expect_delete(ip)
            for (dev_name, if_name) in gateways:
                fqdn = dev_name + '.' + config['domain']
                # We only specify the FQDN when creating the first interface
                command = ["del", "interface", "address",
                           "--network_device", fqdn,
                           "--interface", if_name,
                           "--ip", ip]
                self.noouttest(command)
            if 'skip_dsdb' not in flags:
                self.dsdb_verify()

    def test_806_del_addresses(self):
        if 'skip_delete' in flags:
            return True
        for (dev_name, dev_attrs) in iteritems(config['devices']):
            fqdn = dev_name + '.' + config['domain']
            for (if_name, if_attrs) in iteritems(dev_attrs['interfaces']):
                if if_name == dev_attrs['mgmt_interface']:
                    continue
                net = self.net[if_attrs['net']]
                ip = net[if_attrs['ipidx']]
                self.dsdb_expect_delete(ip)
                command = ["del", "interface", "address",
                           "--network_device", fqdn,
                           "--interface", if_name, "--ip", ip]
                self.noouttest(command)
                if 'skip_dsdb' not in flags:
                    self.dsdb_verify()

    def test_807_del_interfaces(self):
        if 'skip_delete' in flags:
            return True
        for (dev_name, dev_attrs) in iteritems(config['devices']):
            fqdn = dev_name + '.' + config['domain']
            for (if_name, if_attrs) in iteritems(dev_attrs['interfaces']):
                if if_name == dev_attrs['mgmt_interface']:
                    continue
                command = ["del", "interface", "--interface", if_name,
                           "--network_device", fqdn]
                self.noouttest(command)

    def test_808_del_routers(self):
        if 'skip_delete' in flags:
            return True
        for (name, dev_attrs) in iteritems(config['devices']):
            fqdn = name + '.' + config['domain']
            interface = dev_attrs['mgmt_interface']
            if_attrs = dev_attrs['interfaces'][interface]
            net = self.net[if_attrs['net']]
            ip = net[if_attrs['ipidx']]
            self.dsdb_expect_delete(ip)
            command = "del network_device --network_device %s" % fqdn
            self.noouttest(command.split(" "))
            if 'skip_dsdb' not in flags:
                self.dsdb_verify()

    def test_809_del_networks(self):
        if 'skip_delete' in flags:
            return True
        for network in self.net:
            if not network.name.startswith('netuc_'):
                continue
            command = ["del_network", "--ip=%s" % network.ip]
            self.noouttest(command)
            self.check_plenary_gone('network', 'internal', str(network.ip), 'config')

    ########## CLEANUP STAGE ##########

    def test_900_del_6509_model(self):
        if 'skip_prereq' in flags:
            return True
        command = "del model --model cat6509 --vendor cisco"
        self.noouttest(command.split(" "))

    def test_900_del_dns_domain(self):
        if 'skip_prereq' in flags:
            return True
        self.dsdb_expect("delete_dns_domain -domain_name %s" % config['domain'])
        command = "del dns_domain --dns_domain %s" % config['domain']
        self.noouttest(command.split(" "))
        self.dsdb_verify()


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUsecaseNetworks)
    unittest.TextTestRunner(verbosity=2).run(suite)

