#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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
"""Module for testing commands that remove virtual hardware."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDel10GigHardware(TestBrokerCommand):

    def test_200_del_hosts(self):
        for i in range(0, 8) + range(9, 17):
            hostname = "ivirt%d.aqd-unittest.ms.com" % (1 + i)
            command = "del_host --hostname %s" % hostname

            if i < 9:
                net_index = (i % 4) + 2
                usable_index = i / 4
            else:
                net_index = ((i - 9) % 4) + 6
                usable_index = (i - 9) / 4
            ip = self.net.unknown[net_index].usable[usable_index]
            self.dsdb_expect_delete(ip)

            (out, err) = self.successtest(command.split(" "))
            self.assertEmptyOut(out, command)
        self.dsdb_verify()

    def test_300_delaux(self):
        for i in range(1, 25):
            hostname = "evh%d-e1.aqd-unittest.ms.com" % (i + 50)
            self.dsdb_expect_delete(self.net.vm_storage_net[0].usable[i - 1])
            command = ["del", "auxiliary", "--auxiliary", hostname]
            (out, err) = self.successtest(command)
            self.assertEmptyOut(out, command)
        self.dsdb_verify()

    def test_600_delautoassignshares(self):
        for i in range(10, 18):
            self.noouttest(["del", "disk", "--machine", "evm%d" % i,
                            "--disk", "sdc"])

    def test_700_delmachines(self):
        for i in range(0, 8) + range(9, 17):
            machine = "evm%d" % (10 + i)
            self.noouttest(["del", "machine", "--machine", machine])

    def test_800_verifydelmachines(self):
        for i in range(0, 18):
            machine = "evm%d" % (10 + i)
            command = "show machine --machine %s" % machine
            self.notfoundtest(command.split(" "))

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDel10GigHardware)
    unittest.TextTestRunner(verbosity=2).run(suite)
