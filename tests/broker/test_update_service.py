#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010  Contributor
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
"""Module for testing the update service command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUpdateService(TestBrokerCommand):

    def test_100_updateafsservice(self):
        command = "update service --service afs --max_clients 2500"
        self.noouttest(command.split(" "))

    def test_500_verifyupdateafsservice(self):
        command = "show service --service afs"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: afs", command)
        self.matchoutput(out, "Default Maximum Client Count: 2500", command)
        self.matchoutput(out, "Service: afs Instance: q.ny", command)
        self.matchoutput(out, "Maximum Client Count: Default (2500)", command)

    def test_000_preverifybootserverservice(self):
        command = "show service --service bootserver"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: bootserver", command)
        self.matchoutput(out, "Default Maximum Client Count: Unlimited",
                         command)
        self.matchoutput(out, "Service: bootserver Instance: np.test", command)
        self.matchoutput(out, "Maximum Client Count: Default (Unlimited)",
                         command)

    def test_100_updatebootserverservice(self):
        command = "update service --service bootserver --default"
        self.noouttest(command.split(" "))

    def test_500_verifyupdatebootserverservice(self):
        command = "show service --service bootserver"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: bootserver", command)
        self.matchoutput(out, "Default Maximum Client Count: Unlimited",
                         command)
        self.matchoutput(out, "Service: bootserver Instance: np.test", command)
        self.matchoutput(out, "Maximum Client Count: Default (Unlimited)",
                         command)

    def test_600_updatebootserverinstance(self):
        command = ["update_service", "--service=bootserver",
                   "--instance=np.test", "--max_clients=1000"]
        self.noouttest(command)

    def test_700_verifyupdatebootserverservice(self):
        command = "show service --service bootserver"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: bootserver", command)
        self.matchoutput(out, "Default Maximum Client Count: Unlimited",
                         command)
        self.matchoutput(out, "Service: bootserver Instance: np.test", command)
        self.matchoutput(out, "Maximum Client Count: 1000", command)

    def test_100_updateutsvc(self):
        command = "update service --service utsvc --max_clients 1000"
        self.noouttest(command.split(" "))

    def test_200_updateutsi1(self):
        command = ["update_service", "--service=utsvc", "--instance=utsi1",
                   "--max_clients=900"]
        self.noouttest(command)

    def test_500_verifyupdateutsvc(self):
        command = "show service --service utsvc"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: utsvc", command)
        self.matchoutput(out, "Default Maximum Client Count: 1000", command)
        self.matchoutput(out, "Service: utsvc Instance: utsi1", command)
        self.matchoutput(out, "Maximum Client Count: 900", command)
        self.matchoutput(out, "Service: utsvc Instance: utsi2", command)
        self.matchoutput(out, "Maximum Client Count: Default (1000)", command)

    def test_600_updateutsvc(self):
        command = "update service --service utsvc --max_clients 1100"
        self.noouttest(command.split(" "))

    def test_700_verifyupdateutsvc(self):
        command = "show service --service utsvc"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: utsvc", command)
        self.matchoutput(out, "Default Maximum Client Count: 1100", command)
        self.matchoutput(out, "Service: utsvc Instance: utsi1", command)
        self.matchoutput(out, "Maximum Client Count: 900", command)
        self.matchoutput(out, "Service: utsvc Instance: utsi2", command)
        self.matchoutput(out, "Maximum Client Count: Default (1100)", command)

    def test_800_updateutsvc(self):
        command = "update service --service utsvc --instance utsi1 --default"
        self.noouttest(command.split(" "))

    def test_900_verifyupdateutsvc(self):
        command = "show service --service utsvc"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: utsvc", command)
        self.matchoutput(out, "Default Maximum Client Count: 1100", command)
        self.matchoutput(out, "Service: utsvc Instance: utsi1", command)
        self.matchclean(out, "Maximum Client Count: 900", command)
        self.matchoutput(out, "Service: utsvc Instance: utsi2", command)
        self.matchoutput(out, "Maximum Client Count: Default (1100)", command)

    def test_910_updatetestshare1(self):
        command = ["update_service", "--service=nas_disk_share",
        "--instance=test_share_1", "--max_clients=100"]
        self.noouttest(command)

    def test_910_verifypdatetestshare1(self):
        command = ["show_service", "--service=nas_disk_share",
                   "--instance=test_share_1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Maximum Client Count: 100", command)

        command = ["show_nas_disk_share", "--share=test_share_1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Maximum Disk Count: 100", command)
    # FIXME: Missing functionality and tests for plenaries.


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateService)
    unittest.TextTestRunner(verbosity=2).run(suite)

