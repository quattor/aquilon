#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
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
"""Module for testing the bind feature command."""

if __name__ == "__main__":
    from broker import utils
    utils.import_depends()

import unittest2 as unittest
from broker.brokertest import TestBrokerCommand

aquilon_hosts = None
inventory_hosts = None
hs21_hosts = None

hardware_feature_str = r'include {\n'
r'\s*if ((value("/hardware/manufacturer") == "ibm") &&\n'
r'\s*(value("/hardware/template_name") == "hs21-8853l5u")){\n'
r'\s*return("features/hardware/bios_setup")\n'
r'\s*} else{ return(undef); };\n'
r'};'
r'"/metadata/features"={\n'
r'\s*if ((value("/hardware/manufacturer") == "ibm") &&\n'
r'\s(value("/hardware/template_name") == "hs21-8853l5u")){\n'
r'\sappend("features/hardware/bios_setup");\n'
r'\s} else { SELF; };\n'
r'};'


class TestBindFeature(TestBrokerCommand):

    def setUp(self):
        # We don't want to query these for every test executed...
        global aquilon_hosts, inventory_hosts, hs21_hosts

        super(TestBindFeature, self).setUp()

        if aquilon_hosts is None:
            command = ["search", "host", "--archetype", "aquilon",
                       "--format", "proto"]
            out = self.commandtest(command)
            hostlist = self.parse_hostlist_msg(out)
            aquilon_hosts = len(hostlist.hosts)

        if inventory_hosts is None:
            command = ["search", "host", "--personality", "inventory",
                       "--format", "proto"]
            out = self.commandtest(command)
            hostlist = self.parse_hostlist_msg(out)
            inventory_hosts = len(hostlist.hosts)

        if hs21_hosts is None:
            command = ["search", "host", "--archetype", "aquilon",
                       "--model", "hs21-8853l5u", "--format", "proto"]
            out = self.commandtest(command)
            hostlist = self.parse_hostlist_msg(out)
            hs21_hosts = len(hostlist.hosts)

    def test_100_bind_archetype(self):
        command = ["bind", "feature", "--feature", "pre_host",
                   "--archetype", "aquilon",
                   "--justification", "tcm=12345678"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "Flushed 10/10 templates", command)
        # We can't easily check the number of templates that got refreshed since
        # there's no easy way to query if "make" was run for a host or not

    def test_101_verify_show_archetype(self):
        command = ["show", "archetype", "--archetype", "aquilon"]
        out = self.commandtest(command)
        self.matchoutput(out, "Host Feature: pre_host [pre_personality]", command)

    def test_101_verify_show_feature(self):
        command = ["show", "feature", "--feature", "pre_host", "--type", "host"]
        out = self.commandtest(command)
        self.matchoutput(out, "Bound to: Archetype aquilon", command)

    def test_101_verify_show_host(self):
        command = ["show", "host", "--hostname", "unittest00.one-nyp.ms.com"]
        out = self.commandtest(command)
        # Make sure we don't match the feature listed as part of the archetype
        # definition
        self.searchoutput(out,
                          r'^  Host Feature: pre_host \[pre_personality\]$',
                          command)

    def test_101_verify_cat_personality(self):
        command = ["cat", "--personality", "inventory", "--pre_feature"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'include { "features/pre_host/config" };\s*',
                          command)
        self.searchoutput(out,
                          r'"/metadata/features" = append\("features/pre_host/config"\);',
                          command)

    def test_110_bind_personality(self):
        command = ["bind", "feature", "--feature", "post_host",
                   "--personality", "inventory"]
        (out, err) = self.successtest(command)
        self.matchclean(err, "Flushed 10/10", command)

    def test_111_verify_show_personality(self):
        command = ["show", "personality", "--personality", "inventory"]
        out = self.commandtest(command)
        self.matchoutput(out, "Host Feature: post_host [post_personality]",
                         command)

    def test_111_verify_show_personality_proto(self):
        command = ["show", "personality", "--personality", "inventory", "--format=proto"]
        out = self.commandtest(command)
        pl = self.parse_personality_msg(out, 1)
        personality = pl.personalities[0]
        feature = personality.features[0]
        self.failUnlessEqual(feature.name, "post_host")
        self.failUnlessEqual(feature.type, "host")
        self.failUnlessEqual(feature.post_personality, True)
        self.failUnlessEqual(feature.interface_name, "")
        self.failUnlessEqual(feature.model.name, "")
        self.failUnlessEqual(feature.model.vendor, "")

    def test_111_verify_show_feature(self):
        command = ["show", "feature", "--feature", "post_host", "--type", "host"]
        out = self.commandtest(command)
        self.matchoutput(out, "Bound to: Personality aquilon/inventory", command)

    def test_111_verify_show_unittest17(self):
        command = ["show", "host", "--hostname", "unittest17.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        # Make sure we don't match the feature listed as part of the personality
        # definition
        self.matchoutput(out, "Host Personality: inventory", command)
        self.searchoutput(out, r'^  Host Feature: post_host', command)

    def test_111_verify_show_unittest00(self):
        command = ["show", "host", "--hostname", "unittest00.one-nyp.ms.com"]
        out = self.commandtest(command)
        # Make sure we don't match the feature listed as part of the personality
        # definition
        self.matchoutput(out, "Host Personality: compileserver", command)
        self.searchclean(out, r'^  Host Feature: post_host', command)

    def test_111_verify_cat_personality(self):
        command = ["cat", "--personality", "inventory", "--post_feature"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'include { "features/post_host/config" };',
                          command)
        self.searchoutput(out,
                          r'"/metadata/features" = append\("features/post_host/config"\);',
                          command)

    def test_120_bind_personality_redundant(self):
        command = ["bind", "feature", "--feature", "pre_host",
                   "--personality", "inventory"]
        (out, err) = self.successtest(command)
        self.matchoutput(err,
                         "Warning: host feature pre_host is already bound to "
                         "archetype aquilon; binding it to personality "
                         "aquilon/inventory is redundant.",
                         command)
        self.matchoutput(err, "Flushed 1/1 templates.", command)

    def test_121_verify_show_feature(self):
        command = ["show", "feature", "--feature", "pre_host", "--type", "host"]
        out = self.commandtest(command)
        self.matchoutput(out, "Bound to: Archetype aquilon", command)
        self.matchoutput(out, "Bound to: Personality aquilon/inventory", command)

    def test_122_undo_redundant_personality(self):
        command = ["unbind", "feature", "--feature", "pre_host",
                   "--personality", "inventory"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "Flushed 1/1 templates.", command)

    def test_123_verify_undo(self):
        command = ["show", "feature", "--feature", "pre_host", "--type", "host"]
        out = self.commandtest(command)
        self.matchoutput(out, "Bound to: Archetype aquilon", command)
        self.matchclean(out, "inventory", command)

    def test_125_bind_archetype_redundant(self):
        command = ["bind", "feature", "--feature", "post_host",
                   "--archetype", "aquilon", "--justification", "tcm=12345678"]
        (out, err) = self.successtest(command)
        self.matchoutput(err,
                         "Warning: host feature post_host is bound to "
                         "personality aquilon/inventory which is now "
                         "redundant; consider removing it.",
                         command)
        self.matchoutput(err, "Flushed 10/10 templates", command)

    def test_126_verify_show_feature(self):
        command = ["show", "feature", "--feature", "post_host", "--type", "host"]
        out = self.commandtest(command)
        self.matchoutput(out, "Bound to: Archetype aquilon", command)
        self.matchoutput(out, "Bound to: Personality aquilon/inventory", command)

    def test_127_undo_redundant_archetype(self):
        command = ["unbind", "feature", "--feature", "post_host",
                   "--archetype", "aquilon",
                   "--justification", "tcm=12345678"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "Flushed 10/10 templates", command)

    def test_128_verify_undo(self):
        command = ["show", "feature", "--feature", "post_host", "--type", "host"]
        out = self.commandtest(command)
        self.matchoutput(out, "Bound to: Personality aquilon/inventory", command)
        self.matchclean(out, "Bound to: Archetype aquilon", command)

    def test_130_bind_model(self):
        command = ["bind", "feature", "--feature", "bios_setup",
                   "--model", "hs21-8853l5u",
                   "--archetype", "aquilon",
                   "--justification", "tcm=12345678"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "Flushed 10/10 templates.", command)

    def test_131_verify_show_model(self):
        command = ["show", "model", "--model", "hs21-8853l5u"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'Hardware Feature: bios_setup$\n'
                          r'^    Archetype: aquilon$',
                          command)

    def test_131_verify_show_archetype(self):
        command = ["show", "archetype", "--archetype", "aquilon"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'Hardware Feature: bios_setup$\n'
                          r'^    Vendor: ibm Model: hs21-8853l5u$',
                          command)

    def test_131_verify_show_feature(self):
        command = ["show", "feature", "--feature", "bios_setup",
                   "--type", "hardware"]
        out = self.commandtest(command)
        self.matchoutput(out, "Bound to: Model ibm/hs21-8853l5u",
                         command)

    def test_131_verify_show_host(self):
        command = ["show", "host", "--hostname", "unittest02.one-nyp.ms.com"]
        out = self.commandtest(command)
        # Make sure we don't match the feature listed as part of the model
        # definition (we don't do that now, but...)
        self.searchoutput(out, r'^  Hardware Feature: bios_setup$', command)

    def test_131_verify_cat_personality(self):
        command = ["cat", "--personality", "compileserver", "--pre_feature"]
        out = self.commandtest(command)
        # The feature should be after the OS definition
        self.searchoutput(out, hardware_feature_str, command)

    def test_140_bind_nic_model_interface(self):
        command = ["bind", "feature", "--feature", "src_route",
                   "--model", "e1000", "--vendor", "intel",
                   "--personality", "compileserver", "--interface", "eth1"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "Flush", command)

    def test_141_verify_show_model(self):
        command = ["show", "model", "--model", "e1000", "--vendor", "intel"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'Interface Feature: src_route$\n'
                          r'^    Personality: compileserver Archetype: aquilon$\n'
                          r'^    Interface: eth1$',
                          command)

    def test_141_verify_show_personality(self):
        command = ["show", "personality", "--personality", "compileserver"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'Interface Feature: src_route$\n'
                          r'^    Vendor: intel Model: e1000$\n'
                          r'^    Interface: eth1$',
                          command)

    def test_141_verify_show_personality_proto(self):
        command = ["show", "personality", "--personality", "compileserver", "--format=proto"]
        out = self.commandtest(command)
        pl = self.parse_personality_msg(out, 1)
        personality = pl.personalities[0]
        feature = personality.features[0]
        self.failUnlessEqual(feature.name, "src_route")
        self.failUnlessEqual(feature.type, "interface")
        self.failUnlessEqual(feature.post_personality, False)
        self.failUnlessEqual(feature.interface_name, "eth1")
        self.failUnlessEqual(feature.model.name, "e1000")
        self.failUnlessEqual(feature.model.vendor, "intel")

    def test_141_verify_show_feature(self):
        command = ["show", "feature", "--feature", "src_route",
                   "--type", "interface"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Bound to: Model intel/e1000, "
                         "Personality aquilon/compileserver, "
                         "Interface eth1",
                         command)

    def test_141_verify_show_host(self):
        command = ["show", "host", "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.searchclean(out,
                         r'Interface: eth0 .*$\n'
                         r'(^    .*$\n)*'
                         r'^    Template: features/interface/src_route',
                         command)
        self.searchoutput(out,
                          r'Interface: eth1 .*$\n'
                          r'(^    .*$\n)*'
                          r'^    Template: features/interface/src_route',
                          command)

    def test_141_verify_cat_personality(self):
        command = ["cat", "--personality", "compileserver", "--pre_feature"]
        out = self.commandtest(command)
        self.searchclean(out,
                         r'variable CURRENT_INTERFACE = "eth0";\s*'
                         r'include { "features/interface/src_route/config" };',
                         command)
        self.searchoutput(out,
                          r'variable CURRENT_INTERFACE = "eth1";\s*'
                          r'include { "features/interface/src_route/config" };',
                          command)

    def test_141_verify_cat_unittest00(self):
        command = ["cat", "--hostname", "unittest00.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "src_route", command)

    def test_160_bind_interface_personality(self):
        command = ["bind", "feature", "--feature", "src_route",
                   "--personality", "compileserver", "--interface", "bond0"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "Flushed 1/1 templates.", command)

    def test_161_verify_show_personality(self):
        command = ["show", "personality", "--personality", "compileserver"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'Interface Feature: src_route$\n'
                          r'^    Interface: bond0$',
                          command)

    def test_161_verify_show_personality_proto(self):
        command = ["show", "personality", "--personality", "compileserver", "--format=proto"]
        out = self.commandtest(command)
        pl = self.parse_personality_msg(out, 1)
        personality = pl.personalities[0]
        feature = personality.features[0]
        self.failUnlessEqual(feature.name, "src_route")
        self.failUnlessEqual(feature.type, "interface")
        self.failUnlessEqual(feature.post_personality, False)
        self.failUnlessEqual(feature.interface_name, "eth1")
        self.failUnlessEqual(feature.model.name, "e1000")
        self.failUnlessEqual(feature.model.vendor, "intel")
        feature = personality.features[1]
        self.failUnlessEqual(feature.name, "src_route")
        self.failUnlessEqual(feature.type, "interface")
        self.failUnlessEqual(feature.post_personality, False)
        self.failUnlessEqual(feature.interface_name, "bond0")
        self.failUnlessEqual(feature.model.name, "")
        self.failUnlessEqual(feature.model.vendor, "")

    def test_161_verify_show_feature(self):
        command = ["show", "feature", "--feature", "src_route",
                   "--type", "interface"]
        out = self.commandtest(command)
        self.matchoutput(out, 'Bound to: Personality aquilon/compileserver, '
                         'Interface bond0', command)

    def test_161_verify_show_host(self):
        command = ["show", "host", "--hostname", "unittest21.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'Interface: bond0 .*$\n'
                          r'(^    .*$\n)*'
                          r'^    Template: features/interface/src_route',
                          command)

    def test_161_verify_cat_personality(self):
        command = ["cat", "--personality", "compileserver", "--pre_feature"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'variable CURRENT_INTERFACE = "bond0";\s*'
                          r'include { "features/interface/src_route/config" };',
                          command)
        self.matchclean(out, 'variable CURRENT_INTERFACE = "eth0";', command)
        self.matchoutput(out, 'variable CURRENT_INTERFACE = "eth1";', command)

    def test_200_only_interface(self):
        command = ["bind", "feature", "--feature", "src_route",
                   "--interface", "eth0"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Binding to a named interface needs a "
                         "personality.", command)

    def test_200_bind_archetype_again(self):
        command = ["bind", "feature", "--feature", "pre_host",
                   "--archetype", "aquilon",
                   "--justification", "tcm=12345678"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Host Feature pre_host is already bound to "
                         "archetype aquilon.", command)

    def test_200_bind_model_noarch(self):
        command = ["bind", "feature", "--feature", "bios_setup",
                   "--model", "hs21-8853l5u",
                   "--justification", "tcm=12345678"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Please specify either an archetype or a personality "
                         "when binding a feature.",
                         command)

    def test_200_bind_noncompilable_arch(self):
        command = ["bind", "feature", "--feature", "pre_host",
                   "--archetype", "windows",
                   "--justification", "tcm=12345678"]
        out = self.unimplementederrortest(command)
        self.matchoutput(out, "Binding features to non-compilable archetypes "
                         "is not implemented.", command)

    def test_200_bind_model_again(self):
        command = ["bind", "feature", "--feature", "bios_setup",
                   "--model", "hs21-8853l5u",
                   "--archetype", "aquilon",
                   "--justification", "tcm=12345678"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Hardware Feature bios_setup is already bound to "
                         "archetype aquilon, model ibm/hs21-8853l5u.",
                         command)

    def test_200_bind_not_iface(self):
        command = ["bind", "feature", "--feature", "post_host",
                   "--personality", "compileserver", "--interface", "bond0"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Interface Feature post_host not found.", command)

    def test_200_bind_not_host(self):
        command = ["bind", "feature", "--feature", "bios_setup",
                   "--personality", "compileserver"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Host Feature bios_setup not found.", command)

    def test_200_bind_not_hardware(self):
        command = ["bind", "feature", "--feature", "post_host",
                   "--model", "hs21-8853l5u", "--personality", "compileserver"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Hardware Feature post_host not found.", command)

    def test_200_bind_archetype_no_justification(self):
        command = ["bind", "feature", "--feature", "post_host",
                   "--archetype", "aquilon"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,
                         "Changing feature bindings for more than just a "
                         "personality requires --justification.",
                         command)

    def test_200_bind_model_no_justification(self):
        command = ["bind", "feature", "--feature", "disable_ht",
                   "--model", "utmedium", "--archetype", "aquilon"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,
                         "Changing feature bindings for more than just a "
                         "personality requires --justification.",
                         command)

    def test_300_constraint_pre_host(self):
        command = ["del", "feature", "--feature", "pre_host",
                   "--type", "host"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Host Feature pre_host is still in use and cannot be "
                         "deleted.",
                         command)

    def test_300_constraint_post_host(self):
        command = ["del", "feature", "--feature", "post_host",
                   "--type", "host"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Host Feature post_host is still in use and cannot be "
                         "deleted.",
                         command)

    def test_300_constraint_bios_setup(self):
        command = ["del", "feature", "--feature", "bios_setup",
                   "--type", "hardware"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Hardware Feature bios_setup is still in use and cannot be "
                         "deleted.",
                         command)

    def test_300_constraint_src_route(self):
        command = ["del", "feature", "--feature", "src_route",
                   "--type", "interface"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Interface Feature src_route is still in use and cannot be "
                         "deleted.",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBindFeature)
    unittest.TextTestRunner(verbosity=2).run(suite)
