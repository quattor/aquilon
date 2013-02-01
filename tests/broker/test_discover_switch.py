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
"""Module for testing switch discovery."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand
from switchtest import VerifySwitchMixin


class TestDiscoverSwitch(TestBrokerCommand, VerifySwitchMixin):

    def test_100_add_swsync(self):
        ip = self.net.unknown[20].usable[0]
        self.dsdb_expect_add("swsync.aqd-unittest.ms.com", ip, "mgmt0")
        self.noouttest(["add", "switch", "--type", "misc",
                        "--switch", "swsync.aqd-unittest.ms.com",
                        "--interface", "mgmt0", "--ip", ip, "--rack", "ut3",
                        "--model", "temp_switch"])
        self.dsdb_verify()

    def test_110_add_swsync_ifaces(self):
        self.noouttest(["add", "interface", "--switch", "swsync",
                        "--interface", "vlan100"])
        self.noouttest(["add", "interface", "--switch", "swsync",
                        "--interface", "vlan200"])
        self.noouttest(["add", "interface", "--switch", "swsync",
                        "--interface", "vlan300"])
        self.noouttest(["add", "interface", "--switch", "swsync",
                        "--interface", "vlan400"])

    def test_120_add_swsync_addrs(self):
        ip1 = self.net.unknown[20].usable[1]
        ip2 = self.net.unknown[20].usable[2]
        ip3 = self.net.unknown[20].usable[3]
        self.dsdb_expect_add("swsync-vlan100.aqd-unittest.ms.com",
                             ip1, "vlan100",
                             primary="swsync.aqd-unittest.ms.com")
        self.dsdb_expect_add("swsync-nomatch.aqd-unittest.ms.com",
                             ip2, "vlan200",
                             primary="swsync.aqd-unittest.ms.com")
        self.dsdb_expect_add("swsync-vlan300.aqd-unittest.ms.com",
                             ip3, "vlan300",
                             primary="swsync.aqd-unittest.ms.com")
        self.noouttest(["add", "interface", "address", "--switch", "swsync",
                        "--interface", "vlan100", "--ip", ip1,
                        "--fqdn", "swsync-vlan100.aqd-unittest.ms.com"])
        self.noouttest(["add", "interface", "address", "--switch", "swsync",
                        "--interface", "vlan200", "--ip", ip2,
                        "--fqdn", "swsync-nomatch.aqd-unittest.ms.com"])
        self.noouttest(["add", "interface", "address", "--switch", "swsync",
                        "--interface", "vlan300", "--ip", ip3,
                        "--fqdn", "swsync-vlan300.aqd-unittest.ms.com"])
        self.dsdb_verify()

    def test_200_show(self):
        ip1 = self.net.unknown[20].usable[1]
        ip2 = self.net.unknown[20].usable[2]
        ip3 = self.net.unknown[20].usable[3]
        ip4 = self.net.unknown[20].usable[4]
        ip5 = self.net.unknown[20].usable[5]
        command = ["show", "switch", "--switch", "swsync", "--discover"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "aq update_switch --switch swsync.aqd-unittest.ms.com "
                         "--model ws-c2960-48tt-l --vendor cisco "
                         "--comments 'T1 T2'",
                         command)
        self.matchoutput(out, "aq del_interface_address "
                         "--switch swsync.aqd-unittest.ms.com "
                         "--interface vlan100 --ip %s" % ip1, command)
        self.matchoutput(out, "aq del_interface "
                         "--switch swsync.aqd-unittest.ms.com "
                         "--interface vlan400", command)
        self.matchoutput(out, "aq update_interface "
                         "--switch swsync.aqd-unittest.ms.com "
                         "--interface vlan200 --rename_to vlan210", command)
        self.matchoutput(out, "aq update_interface "
                         "--switch swsync.aqd-unittest.ms.com "
                         "--interface vlan300 --rename_to vlan310", command)
        self.matchoutput(out, "aq add_interface_address "
                         "--switch swsync.aqd-unittest.ms.com "
                         "--interface vlan100 --ip %s --label hsrp" % ip1,
                         command)
        self.matchoutput(out, "aq add_interface_address "
                         "--switch swsync.aqd-unittest.ms.com "
                         "--interface vlan100 --ip %s" % ip4, command)
        self.matchoutput(out, "aq add_interface "
                         "--switch swsync.aqd-unittest.ms.com "
                         "--interface vlan500 --type oa", command)
        self.matchoutput(out, "aq add_interface_address "
                         "--switch swsync.aqd-unittest.ms.com "
                         "--interface vlan500 --ip %s" % ip5, command)
        self.matchoutput(out, "qip-set-router %s" % ip1, command)

    def test_210_update(self):
        ip1 = self.net.unknown[20].usable[1]
        ip4 = self.net.unknown[20].usable[4]
        ip5 = self.net.unknown[20].usable[5]
        self.dsdb_expect_update("swsync.aqd-unittest.ms.com",
                                "mgmt0", comments="T1 T2")
        self.dsdb_expect_update("swsync-vlan100.aqd-unittest.ms.com",
                                "vlan100", ip4, comments="T1 T2")
        self.dsdb_expect_add("swsync-vlan100-hsrp.aqd-unittest.ms.com", ip1,
                             "vlan100_hsrp", comments="T1 T2",
                             primary="swsync.aqd-unittest.ms.com")
        self.dsdb_expect_update("swsync-nomatch.aqd-unittest.ms.com",
                                "vlan200", comments="T1 T2")
        self.dsdb_expect_update("swsync-vlan300.aqd-unittest.ms.com",
                                "vlan300", comments="T1 T2")
        self.dsdb_expect_rename("swsync-nomatch.aqd-unittest.ms.com",
                                iface="vlan200", new_iface="vlan210")
        self.dsdb_expect_rename("swsync-vlan300.aqd-unittest.ms.com",
                                "swsync-vlan310.aqd-unittest.ms.com",
                                "vlan300", "vlan310")
        self.dsdb_expect_add("swsync-vlan500.aqd-unittest.ms.com", ip5,
                             "vlan500", comments="T1 T2",
                             primary="swsync.aqd-unittest.ms.com")
        command = ["update", "switch", "--switch", "swsync", "--discover"]
        out, err = self.successtest(command)
        self.matchoutput(err,
                         "Using jump host nyaqd1.ms.com from service instance "
                         "poll_helper/unittest to run CheckNet for switch "
                         "swsync.aqd-unittest.ms.com.",
                         command)
        self.matchoutput(err, "You should run 'qip-set-router %s'." % ip1,
                         command)
        self.dsdb_verify()

    def test_300_verify(self):
        ip = self.net.unknown[20].usable[0]
        ip1 = self.net.unknown[20].usable[1]
        ip2 = self.net.unknown[20].usable[2]
        ip3 = self.net.unknown[20].usable[3]
        ip4 = self.net.unknown[20].usable[4]
        ip5 = self.net.unknown[20].usable[5]
        out, command = self.verifyswitch("swsync.aqd-unittest.ms.com",
                                         "cisco", "ws-c2960-48tt-l", "ut3", "a",
                                         "3", switch_type="misc",
                                         ip=self.net.unknown[20].usable[0],
                                         interface="mgmt0",
                                         comments="T1 T2")
        # TODO: the interface type is not updated, it's not clear if it should
        self.searchoutput(out,
                          r"Interface: mgmt0 \(no MAC addr\)\s*"
                          r"Type: oa\s*"
                          r"Network Environment: internal\s*"
                          r"Provides: swsync.aqd-unittest.ms.com \[%s\]"
                          % ip, command)
        self.searchoutput(out,
                          r"Interface: vlan100 \(no MAC addr\)\s*"
                          r"Type: oa\s*"
                          r"Network Environment: internal\s*"
                          r"Provides: swsync-vlan100.aqd-unittest.ms.com \[%s\]\s*"
                          r"Provides: swsync-vlan100-hsrp.aqd-unittest.ms.com \[%s\] \(label: hsrp\)"
                          % (ip4, ip1), command)
        self.searchoutput(out,
                          r"Interface: vlan210 \(no MAC addr\)\s*"
                          r"Type: oa\s*"
                          r"Network Environment: internal\s*"
                          r"Provides: swsync-nomatch.aqd-unittest.ms.com \[%s\]"
                          % ip2, command)
        self.searchoutput(out,
                          r"Interface: vlan310 \(no MAC addr\)\s*"
                          r"Type: oa\s*"
                          r"Network Environment: internal\s*"
                          r"Provides: swsync-vlan310.aqd-unittest.ms.com \[%s\]"
                          % ip3, command)
        self.searchoutput(out,
                          r"Interface: vlan500 \(no MAC addr\)\s*"
                          r"Type: oa\s*"
                          r"Network Environment: internal\s*"
                          r"Provides: swsync-vlan500.aqd-unittest.ms.com \[%s\]"
                          % ip5, command)

    def test_400_del_swsync_addrs(self):
        ip1 = self.net.unknown[20].usable[1]
        ip2 = self.net.unknown[20].usable[2]
        ip3 = self.net.unknown[20].usable[3]
        ip4 = self.net.unknown[20].usable[4]
        ip5 = self.net.unknown[20].usable[5]
        self.dsdb_expect_delete(ip1)
        self.dsdb_expect_delete(ip2)
        self.dsdb_expect_delete(ip3)
        self.dsdb_expect_delete(ip4)
        self.dsdb_expect_delete(ip5)
        self.noouttest(["del", "interface", "address", "--switch", "swsync",
                        "--interface", "vlan100", "--ip", ip1])
        self.noouttest(["del", "interface", "address", "--switch", "swsync",
                        "--interface", "vlan100", "--ip", ip4])
        self.noouttest(["del", "interface", "address", "--switch", "swsync",
                        "--interface", "vlan210", "--ip", ip2])
        self.noouttest(["del", "interface", "address", "--switch", "swsync",
                        "--interface", "vlan310", "--ip", ip3])
        self.noouttest(["del", "interface", "address", "--switch", "swsync",
                        "--interface", "vlan500", "--ip", ip5])
        self.dsdb_verify()

    def test_410_del_swsync(self):
        self.dsdb_expect_delete(self.net.unknown[20].usable[0])
        self.noouttest(["del", "switch", "--switch", "swsync"])
        self.dsdb_verify()


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDiscoverSwitch)
    unittest.TextTestRunner(verbosity=2).run(suite)
