#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
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
"""Module for testing the del feature command."""


import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelFeature(TestBrokerCommand):

    def test_100_del_host_pre(self):
        command = ["del", "feature", "--feature", "pre_host", "--type", "host"]
        self.noouttest(command)

    def test_100_del_host_post(self):
        command = ["del", "feature", "--feature", "post_host", "--type", "host"]
        self.noouttest(command)

    def test_100_del_hw(self):
        command = ["del", "feature", "--feature", "bios_setup",
                   "--type", "hardware"]
        self.noouttest(command)

    def test_100_del_hw2(self):
        command = ["del", "feature", "--feature", "disable_ht",
                   "--type", "hardware"]
        self.noouttest(command)

    def test_100_del_iface(self):
        command = ["del", "feature", "--feature", "src_route",
                   "--type", "interface"]
        self.noouttest(command)

    def test_110_verify_pre(self):
        command = ["show", "feature", "--feature", "pre_host", "--type", "host"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Host Feature pre_host not found.", command)

    def test_110_verify_post(self):
        command = ["show", "feature", "--feature", "post_host",
                   "--type", "host"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Host Feature post_host not found.", command)

    def test_110_verify_hw(self):
        command = ["show", "feature", "--feature", "bios_setup",
                   "--type", "hardware"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Hardware Feature bios_setup not found.", command)

    def test_110_verify_iface(self):
        command = ["show", "feature", "--feature", "src_route",
                   "--type", "interface"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Interface Feature src_route not found.", command)

    def test_120_show_all(self):
        command = ["show", "feature", "--all"]
        out = self.commandtest(command)
        self.matchclean(out, "pre_host", command)
        self.matchclean(out, "post_host", command)
        self.matchclean(out, "bios_setup", command)
        self.matchclean(out, "src_route", command)

    def test_200_del_again(self):
        command = ["del", "feature", "--feature", "bios_setup",
                   "--type", "hardware"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Hardware Feature bios_setup not found.", command)

    def test_210_del_bad_type(self):
        command = ["del", "feature", "--feature", "bad-type",
                   "--type", "no-such-type"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Unknown feature type 'no-such-type'.  The "
                         "valid types are: hardware, host, interface.",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelFeature)
    unittest.TextTestRunner(verbosity=2).run(suite)
