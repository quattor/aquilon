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
"""Module for testing the update chassis command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand
from chassistest import VerifyChassisMixin


class TestUpdateChassis(TestBrokerCommand, VerifyChassisMixin):

    def test_100_update_ut3c5(self):
        ip = self.net.unknown[0].usable[6]
        self.dsdb_expect_add("ut3c5.aqd-unittest.ms.com", ip, "oa")
        self.dsdb_expect_update_comment("ut3c5.aqd-unittest.ms.com",
                                        "Some new chassis comments")
        command = ["update", "chassis", "--chassis", "ut3c5.aqd-unittest.ms.com",
                   "--rack", "ut3", "--serial", "ABC5678",
                   "--model", "c-class", "--ip", ip,
                   "--comments", "Some new chassis comments"]
        self.noouttest(command)

    def test_110_verify_ut3c5(self):
        self.verifychassis("ut3c5.aqd-unittest.ms.com", "hp", "c-class",
                           "ut3", "a", "3", "ABC5678",
                           comments="Some new chassis comments",
                           ip=self.net.unknown[0].usable[6])

    def test_200_update_bad_ip(self):
        ip = self.net.unknown[0].usable[6]
        command = ["update", "chassis", "--ip", ip,
                   "--chassis", "ut3c1.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                          "IP address %s is already in use by on-board admin "
                          "interface oa of chassis "
                          "ut3c5.aqd-unittest.ms.com." % ip,
                          command)

    def test_200_update_bad_model(self):
        command = ["update", "chassis", "--model", "uttorswitch",
                   "--chassis", "ut3c1.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Model uttorswitch, machine_type chassis not found.",
                         command)

    def test_200_not_chassis(self):
        command = ["update", "chassis", "--chassis",
                   "ut3gd1r01.aqd-unittest.ms.com",
                   "--comments", "Not a chassis"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Switch ut3gd1r01.aqd-unittest.ms.com exists, but "
                         "is not a chassis.",
                         command)

    def test_200_no_model(self):
        command = ["update", "chassis", "--vendor", "generic",
                   "--chassis", "ut3c1.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Model utchassis, vendor generic, "
                         "machine_type chassis not found.",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateChassis)
    unittest.TextTestRunner(verbosity=2).run(suite)
