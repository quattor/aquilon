#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013,2014,2015,2016,2017  Contributor
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

import re
import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUnbindFeature(TestBrokerCommand):

    def verify_personality_flush(self, err, orig_command):
        command = ["search", "personality", "--archetype", "aquilon"]
        perslist = self.commandtest(command).splitlines()
        self.matchoutput(err, "Flushed %d/%d templates" %
                         (len(perslist), len(perslist)), orig_command)

    def test_100_unbind_redundant_personality(self):
        command = ["unbind", "feature", "--feature", "pre_host",
                   "--personality", "inventory"]
        err = self.statustest(command)
        # Parameters should be gone even if the feature is still bound at the
        # archetype level
        self.matchoutput(err, "Flushed 1/1 templates.", command)

    def test_101_verify_still_there(self):
        command = ["show", "feature", "--feature", "pre_host", "--type", "host"]
        out = self.commandtest(command)
        self.matchoutput(out, "Bound to: Archetype aquilon", command)
        self.matchclean(out, "inventory", command)

        command = ["cat", "--personality", "inventory"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'include { "features/pre_host/config" };',
                          command)
        self.matchclean(out, "system/features/pre_host", command)

    def test_105_unbind_archetype(self):
        command = ["unbind", "feature", "--feature", "pre_host",
                   "--archetype", "aquilon",
                   "--justification", "tcm=12345678"]
        err = self.statustest(command)
        self.verify_personality_flush(err, command)

    def test_106_verify_archetype(self):
        command = ["show", "archetype", "--archetype", "aquilon"]
        out = self.commandtest(command)
        self.searchclean(out, "pre_host$", command)

    def test_106_verify_feature(self):
        command = ["show", "feature", "--feature", "pre_host", "--type", "host"]
        out = self.commandtest(command)
        self.matchclean(out, "Bound to: Archetype aquilon", command)

    def test_106_verify_show_host(self):
        command = ["show", "host", "--hostname", "unittest00.one-nyp.ms.com"]
        out = self.commandtest(command)
        # Make sure we don't match the feature listed as part of the archetype
        # definition
        self.searchclean(out, r'^  Host Feature: pre_host$', command)

    def test_106_verify_cat_personality(self):
        command = ["cat", "--personality", "inventory"]
        out = self.commandtest(command)
        self.matchclean(out, "pre_host/config", command)

    def test_110_unbind_redundant_archetype(self):
        command = ["unbind", "feature", "--feature", "post_host",
                   "--archetype", "aquilon",
                   "--justification", "tcm=12345678"]
        err = self.statustest(command)
        matches = re.search(r"Flushed (\d+)/(\d+) templates", err, re.M)
        # The inventory personality should not have changed
        self.assertEqual(int(matches.group(1)) + 1, int(matches.group(2)))

    def test_111_verify_archetype(self):
        command = ["show", "archetype", "--archetype", "aquilon"]
        out = self.commandtest(command)
        self.searchclean(out, "post_host$", command)

    def test_111_verify_show_feature(self):
        command = ["show", "feature", "--feature", "post_host", "--type", "host"]
        out = self.commandtest(command)
        self.matchoutput(out, "Bound to: Personality aquilon/inventory", command)
        self.matchclean(out, "Bound to: Archetype aquilon", command)

    def test_111_verify_cat_personality(self):
        command = ["cat", "--personality", "inventory"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'include { "features/post_host/config" };',
                          command)

    def test_115_unbind_personality(self):
        command = ["unbind", "feature", "--feature", "post_host",
                   "--personality", "inventory"]
        err = self.statustest(command)
        self.matchoutput(err, "Flushed 1/1 templates.", command)

    def test_116_verify_show_personality(self):
        command = ["show_personality", "--personality", "inventory"]
        out = self.commandtest(command)
        self.matchclean(out, "post_host", command)

    def test_116_verify_cat_personality(self):
        command = ["cat", "--personality", "inventory"]
        out = self.commandtest(command)
        self.matchclean(out, "post_host/config", command)

    def test_130_unbind_model_personality(self):
        self.statustest(["unbind_feature", "--feature", "bios_setup",
                         "--personality", "compileserver", "--archetype", "aquilon",
                         "--model", "hs21-8853"])

    def test_131_verify_params_gone(self):
        command = ["show_parameter", "--personality", "compileserver",
                   "--archetype", "aquilon"]
        out = self.commandtest(command)
        self.matchclean(out, "bios_setup", command)

    def test_132_unbind_model_archetype(self):
        hosts = self.commandtest(["search_host", "--archetype", "aquilon",
                                  "--model", "hs21-8853"]).splitlines()

        command = ["unbind", "feature", "--feature", "bios_setup",
                   "--model", "hs21-8853",
                   "--archetype", "aquilon",
                   "--justification", "tcm=12345678"]
        err = self.statustest(command)
        # The actual number of templates written may be different, because not
        # all the hosts have services assigned, so sometimes only
        # PlenaryHostData gets written and not PlenaryHostObject.
        self.searchoutput(err, r"Flushed \d+/%d templates" % len(hosts),
                          command)

    def test_135_verify_show_model(self):
        command = ["show", "model", "--model", "hs21-8853"]
        out = self.commandtest(command)
        self.matchclean(out, "bios_setup", command)

    def test_135_verify_show_feature(self):
        command = ["show", "feature", "--feature", "bios_setup",
                   "--type", "hardware"]
        out = self.commandtest(command)
        self.matchclean(out, "hs21-8853", command)

    def test_135_verify_show_unittest02(self):
        command = ["show", "host", "--hostname", "unittest02.one-nyp.ms.com"]
        out = self.commandtest(command)
        # Make sure we don't match the feature listed as part of the model
        # definition (we don't do that now, but...)
        self.searchclean(out, r'^  Hardware Feature: bios_setup$', command)

    def test_135_verify_cat_unittest02(self):
        command = ["cat", "--hostname", "unittest02.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "bios_setup", command)

    def test_140_unbind_nic_model_interface(self):
        command = ["unbind", "feature", "--feature", "src_route",
                   "--model", "e1000", "--vendor", "intel",
                   "--personality", "compileserver",
                   "--interface", "eth1", "--justification", "tcm=12345678"]
        err = self.statustest(command)
        self.matchoutput(err, "Flush", command)

    def test_141_check_param_exists(self):
        command = ["show_parameter", "--personality", "compileserver",
                   "--archetype", "aquilon"]
        out = self.commandtest(command)
        self.matchoutput(out, 'testdefault: "interface_feature"', command)

    def test_145_unbind_nic_model_2nd_interface(self):
        command = ["unbind", "feature", "--feature", "src_route",
                   "--personality", "compileserver", "--interface", "bond0",
                   "--justification", "tcm=12345678"]
        err = self.statustest(command)
        self.matchoutput(err, "Flushed 2/1 templates.", command)

    def test_146_verify_show_feature(self):
        command = ["show", "feature", "--feature", "src_route",
                   "--type", "interface"]
        out = self.commandtest(command)
        self.searchclean(out, "Interface bond0", command)

    def test_146_verify_show_unittest21(self):
        command = ["show", "host", "--hostname", "unittest21.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.searchclean(out,
                         r'Interface: bond0 .*$\n'
                         r'(^    .*$\n)*'
                         r'^    Template: features/interface/src_route',
                         command)

    def test_146_verify_cat_unittest21(self):
        command = ["cat", "--hostname", "unittest21.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, 'src_route', command)

    def test_146_check_param_gone(self):
        command = ["show_parameter", "--personality", "compileserver",
                   "--archetype", "aquilon"]
        out = self.commandtest(command)
        self.matchclean(out, 'testdefault', command)

    def test_150_unbind_same_feature_name(self):
        for type in ["host", "hardware", "interface"]:
            cmd = ["unbind_feature", "--feature", "shinynew", "--personality", "inventory"]
            if type == "interface":
                cmd.extend(["--interface", "eth0"])
            if type == "hardware":
                cmd.extend(["--model", "hs21-8853"])
            self.successtest(cmd)

    def test_200_unbind_archetype_again(self):
        command = ["unbind", "feature", "--feature", "pre_host",
                   "--archetype", "aquilon",
                   "--justification", "tcm=12345678"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Host Feature pre_host is not bound to "
                         "archetype aquilon.",
                         command)

    def test_200_unbind_interface_personality_again(self):
        command = ["unbind", "feature", "--feature", "src_route",
                   "--personality", "compileserver", "--interface", "bond0",
                   "--justification", "tcm=12345678"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Interface Feature src_route is not bound to "
                         "personality aquilon/compileserver, interface bond0.",
                         command)

    def test_900_verify_no_bindings(self):
        # Leftover bindings will cause subsequent compiles to fail as we don't
        # have the templates, so make sure nothing is left
        command = ["show", "feature", "--all"]
        out = self.commandtest(command)
        self.matchclean(out, "Bound to", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUnbindFeature)
    unittest.TextTestRunner(verbosity=2).run(suite)
