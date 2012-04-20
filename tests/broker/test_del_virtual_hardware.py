#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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


class TestDelVirtualHardware(TestBrokerCommand):

    def test_200_del_windows_hosts(self):
        command = "del_host --hostname aqddesk1.msad.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)

    def test_300_readd_windows_host(self):
        command = ["add_windows_host", "--hostname=aqdtop1.msad.ms.com",
                   "--machine=evm1", "--comments=Windows Virtual Desktop"]
        self.noouttest(command)

    def test_400_reverify_windows_host(self):
        command = "show host --hostname aqdtop1.msad.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Primary Name: aqdtop1.msad.ms.com", command)
        self.matchoutput(out, "Virtual_machine: evm1", command)
        self.matchoutput(out, "Comments: Windows Virtual Desktop", command)

    def test_500_redel_windows_hosts(self):
        command = "del_host --hostname aqdtop1.msad.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)

    def test_700_delmachines(self):
        for i in range(1, 10) + \
                 range(50, 63) + range(70, 83) + \
                 range(90, 103) + range(110, 123):
            self.noouttest(["del", "machine", "--machine", "evm%s" % i])

    def test_800_verifydelmachines(self):
        for i in range(1, 10) + \
                 range(50, 63) + range(70, 83) + \
                 range(90, 103) + range(110, 123):
            command = "show machine --machine evm%s" %i
            self.notfoundtest(command.split(" "))

    # Hack... doing this test here for timing reasons...
    def test_900_verifydelclusterwithmachines(self):
        command = "del esx cluster --cluster utecl1"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Cluster utecl1 is still in use by hosts",
                         command)

    def test_800_verifycatcluster(self):
        command = "cat --cluster=utecl1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "object template clusters/utecl1;", command)
        self.searchoutput(out,
                          r'include { "service/esx_management_server/ut.[ab]/client/config" };',
                          command)

        command = "cat --cluster=utecl1 --data"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"/system/cluster/name" = "utecl1";', command)
        self.matchoutput(out, '"/system/metacluster/name" = "utmc1";', command)
        self.searchoutput(out, r'"/system/cluster/machines" = nlist\(\s*\);',
                          command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelVirtualHardware)
    unittest.TextTestRunner(verbosity=2).run(suite)

