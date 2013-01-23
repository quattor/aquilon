#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
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
"""Module for testing the bind feature command."""


import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUnbindFeature(TestBrokerCommand):

    def setUp(self):
        super(TestUnbindFeature, self).setUp()

    def test_100_unbind_archetype(self):
        command = ["unbind", "feature", "--feature", "pre_host",
                   "--archetype", "aquilon",
                   "--justification", "tcm=12345678"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "Flushed 10/10 templates.", command)

    def test_101_verify_archetype(self):
        command = ["show", "archetype", "--archetype", "aquilon"]
        out = self.commandtest(command)
        self.matchclean(out, "Host Feature: pre_host", command)

    def test_101_verify_feature(self):
        command = ["show", "feature", "--feature", "pre_host", "--type", "host"]
        out = self.commandtest(command)
        self.matchclean(out, "Bound to: Archetype aquilon", command)

    def test_101_verify_show_host(self):
        command = ["show", "host", "--hostname", "unittest00.one-nyp.ms.com"]
        out = self.commandtest(command)
        # Make sure we don't match the feature listed as part of the archetype
        # definition
        self.searchclean(out, r'^  Host Feature: pre_host$', command)

    def test_101_verify_cat_personality(self):
        command = ["cat", "--personality", "inventory", "--pre_feature"]
        out = self.commandtest(command)
        self.matchclean(out, "pre_host", command)

    def test_110_unbind_personality(self):
        command = ["unbind", "feature", "--feature", "post_host",
                   "--personality", "inventory"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "Flushed 1/1 templates.", command)

    def test_130_unbind_model(self):
        command = ["unbind", "feature", "--feature", "bios_setup",
                   "--model", "hs21-8853l5u",
                   "--archetype", "aquilon",
                   "--justification", "tcm=12345678"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "Flushed 10/10 templates.", command)

    def test_131_verify_show_model(self):
        command = ["show", "model", "--model", "hs21-8853l5u"]
        out = self.commandtest(command)
        self.matchclean(out, "bios_setup", command)

    def test_131_verify_show_feature(self):
        command = ["show", "feature", "--feature", "bios_setup",
                   "--type", "hardware"]
        out = self.commandtest(command)
        self.matchclean(out, "hs21-8853l5u", command)

    def test_131_verify_show_host(self):
        command = ["show", "host", "--hostname", "unittest02.one-nyp.ms.com"]
        out = self.commandtest(command)
        # Make sure we don't match the feature listed as part of the model
        # definition (we don't do that now, but...)
        self.searchclean(out, r'^  Hardware Feature: bios_setup$', command)

    def test_131_verify_cat_personality(self):
        command = ["cat", "--personality", "compileserver", "--pre_feature"]
        out = self.commandtest(command)
        self.matchclean(out, "bios_setup", command)

    def test_140_unbind_nic_model_interface(self):
        command = ["unbind", "feature", "--feature", "src_route",
                   "--model", "e1000", "--vendor", "intel",
                   "--personality", "compileserver",
                   "--interface", "eth1"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "Flush", command)

    def test_160_unbind_interface_personality(self):
        command = ["unbind", "feature", "--feature", "src_route",
                   "--personality", "compileserver", "--interface", "bond0"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "Flushed 1/1 templates.", command)

    def test_161_verify_show_feature(self):
        command = ["show", "feature", "--feature", "src_route",
                   "--type", "interface"]
        out = self.commandtest(command)
        self.searchclean(out, "Interface bond0", command)

    def test_161_verify_show_host(self):
        command = ["show", "host", "--hostname", "unittest21.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.searchclean(out,
                         r'Interface: bond0 .*$\n'
                         r'(^    .*$\n)*'
                         r'^    Template: features/interface/src_route',
                         command)

    def test_161_verify_cat_personality(self):
        command = ["cat", "--personality", "compileserver", "--pre_feature"]
        out = self.commandtest(command)
        self.matchclean(out, 'bond0', command)
        self.matchclean(out, 'src_route', command)

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
                   "--personality", "compileserver", "--interface", "bond0"]
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
