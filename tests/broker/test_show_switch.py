#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010  Contributor
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
"""Module for testing the show switch command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestShowSwitch(TestBrokerCommand):

    def testshowswitchall(self):
        command = ["show_switch", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "Switch: ut3gd1r01", command)
        self.matchoutput(out,
                         "Primary Name: ut3gd1r01.aqd-unittest.ms.com [%s]" %
                         self.net.tor_net[0].usable[0],
                         command)
        self.matchoutput(out, "Switch Type: bor", command)
        self.matchoutput(out, "Rack: ut3", command)
        self.matchoutput(out, "Vendor: hp Model: uttorswitch", command)
        self.matchoutput(out, "Serial: SNgd1r01", command)
        self.matchoutput(out, "Switch: ut3gd1r04", command)
        self.matchoutput(out,
                         "Primary Name: ut3gd1r04.aqd-unittest.ms.com [%s]" %
                         self.net.tor_net[6].usable[1],
                         command)
        self.matchoutput(out, "Switch Type: tor", command)

    def testshowswitchswitch(self):
        command = ["show_switch", "--switch=ut3gd1r04.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Switch: ut3gd1r04", command)
        self.matchoutput(out,
                         "Primary Name: ut3gd1r04.aqd-unittest.ms.com [%s]" %
                         self.net.tor_net[6].usable[1],
                         command)
        self.matchoutput(out, "Switch Type: bor", command)
        self.matchoutput(out, "Rack: ut3", command)
        self.matchoutput(out, "Vendor: hp Model: uttorswitch", command)

    def testshowswitchallcsv(self):
        # Verify both with and without an interface
        command = ["show_switch", "--all", "--format=csv"]

    def testshowswitchswitchcsv(self):
        command = ["show_switch", "--switch=ut3gd1r04.aqd-unittest.ms.com",
                   "--format=csv"]


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestShowSwitch)
    unittest.TextTestRunner(verbosity=2).run(suite)
