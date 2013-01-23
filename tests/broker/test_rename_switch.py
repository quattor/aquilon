#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
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
"""Module for testing the update switch command."""

import os.path
import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand
from switchtest import VerifySwitchMixin


class TestRenameSwitch(TestBrokerCommand, VerifySwitchMixin):

    def test_100_rename_ut3gd1r04(self):
        self.dsdb_expect_rename("ut3gd1r04-vlan110-hsrp.aqd-unittest.ms.com",
                                "renametest-vlan110-hsrp.aqd-unittest.ms.com")
        self.dsdb_expect_rename("ut3gd1r04-vlan110.aqd-unittest.ms.com",
                                "renametest-vlan110.aqd-unittest.ms.com")
        self.dsdb_expect_rename("ut3gd1r04-loop0.aqd-unittest.ms.com",
                                "renametest-loop0.aqd-unittest.ms.com")
        self.dsdb_expect_rename("ut3gd1r04.aqd-unittest.ms.com",
                                "renametest.aqd-unittest.ms.com")

        pdir = os.path.join(self.config.get("broker", "plenarydir"),
                            "switchdata")
        old_plenary = os.path.join(pdir, "ut3gd1r04.aqd-unittest.ms.com.tpl")
        new_plenary = os.path.join(pdir, "renametest.aqd-unittest.ms.com.tpl")

        self.failUnless(os.path.exists(old_plenary),
                        "Plenary file '%s' does not exist" % old_plenary)

        command = ["update", "switch",
                   "--switch", "ut3gd1r04.aqd-unittest.ms.com",
                   "--rename_to", "renametest"]
        self.noouttest(command)

        self.failIf(os.path.exists(old_plenary),
                    "Plenary file '%s' still exists" % old_plenary)
        self.failUnless(os.path.exists(new_plenary),
                        "Plenary file '%s' does not exist" % new_plenary)

        self.dsdb_verify()

    def test_110_verify(self):
        self.verifyswitch("renametest.aqd-unittest.ms.com", "hp", "uttorswitch",
                          "ut3", "a", "3", switch_type='bor',
                          ip=self.net.tor_net[6].usable[1],
                          mac=self.net.tor_net[6].usable[0].mac,
                          interface="xge49",
                          comments="Some new switch comments")

    def test_200_rename_ut3gd1r04_back(self):
        self.dsdb_expect_rename("renametest-vlan110-hsrp.aqd-unittest.ms.com",
                                "ut3gd1r04-vlan110-hsrp.aqd-unittest.ms.com")
        self.dsdb_expect_rename("renametest-vlan110.aqd-unittest.ms.com",
                                "ut3gd1r04-vlan110.aqd-unittest.ms.com")
        self.dsdb_expect_rename("renametest-loop0.aqd-unittest.ms.com",
                                "ut3gd1r04-loop0.aqd-unittest.ms.com")
        self.dsdb_expect_rename("renametest.aqd-unittest.ms.com",
                                "ut3gd1r04.aqd-unittest.ms.com")

        command = ["update", "switch",
                   "--switch", "renametest",
                   "--rename_to", "ut3gd1r04.aqd-unittest.ms.com"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_210_verify(self):
        self.verifyswitch("ut3gd1r04.aqd-unittest.ms.com", "hp", "uttorswitch",
                          "ut3", "a", "3", switch_type='bor',
                          ip=self.net.tor_net[6].usable[1],
                          mac=self.net.tor_net[6].usable[0].mac,
                          interface="xge49",
                          comments="Some new switch comments")

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRenameSwitch)
    unittest.TextTestRunner(verbosity=2).run(suite)
