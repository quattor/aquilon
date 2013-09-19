#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2012,2013  Contributor
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
"""Module for testing the update service command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
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
        self.matchoutput(out, "Service: bootserver Instance: one-nyp", command)
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
        self.matchoutput(out, "Service: bootserver Instance: one-nyp", command)
        self.matchoutput(out, "Maximum Client Count: Default (Unlimited)",
                         command)

    def test_600_updatebootserverinstance(self):
        command = ["update_service", "--service=bootserver",
                   "--instance=one-nyp", "--max_clients=1000"]
        self.noouttest(command)

    def test_700_verifyupdatebootserverservice(self):
        command = "show service --service bootserver"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: bootserver", command)
        self.matchoutput(out, "Default Maximum Client Count: Unlimited",
                         command)
        self.matchoutput(out, "Service: bootserver Instance: one-nyp", command)
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

    # FIXME: Missing functionality and tests for plenaries.


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateService)
    unittest.TextTestRunner(verbosity=2).run(suite)
