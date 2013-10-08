#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Module for testing the del service command."""

import os.path

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestDelService(TestBrokerCommand):

    def testdelafsinstance(self):
        command = "del service --service afs --instance q.ny.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelafsinstance(self):
        command = "show service --service afs"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Service: afs Instance: q.ny.ms.com", command)

    def testdelafsbynetinstance(self):
        command = "del service --service afs --instance afs-by-net"
        self.noouttest(command.split(" "))

        command = "del service --service afs --instance afs-by-net2"
        self.noouttest(command.split(" "))

    def testverifydelafsbynetinstance(self):
        command = "show service --service afs"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Service: afs Instance: afs-by-net", command)

    def testdelnetmappersinstance(self):
        command = "del service --service netmap --instance netmap-pers"
        self.noouttest(command.split(" "))

        command = "del service --service netmap --instance q.ny.ms.com"
        self.noouttest(command.split(" "))

        command = "del service --service netmap --instance p-q.ny.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelnetmappersinstance(self):
        command = "show service --service netmap"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Service: netmap Instance: netmap-pers", command)
        self.matchclean(out, "Service: netmap Instance: q.ny.ms.com", command)
        self.matchclean(out, "Service: netmap Instance: p-q.ny.ms.com", command)

    def testdelextraafsinstance(self):
        command = "del service --service afs --instance q.ln.ms.com"
        self.notfoundtest(command.split(" "))

    def testverifydelextraafsinstance(self):
        command = "show service --service afs"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Service: afs Instance: q.ln.ms.com", command)

    def testdelbootserverinstance(self):
        self.noouttest(["del_service", "--service", "bootserver", "--instance", "one-nyp"])
        self.noouttest(["del_service", "--service", "bootserver", "--instance", "unittest"])

    def testverifydelbootserverinstance(self):
        command = "show service --service bootserver"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "one-nyp", command)
        self.matchclean(out, "unittest", command)

    def testdellemoninstance(self):
        command = "del service --service lemon --instance ny-prod"
        self.noouttest(command.split(" "))

    def testverifydellemoninstance(self):
        command = "show service --service lemon"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Service: lemon Instance: ny-prod", command)

    def testdeldnsinstance(self):
        command = "del service --service dns --instance unittest"
        self.noouttest(command.split(" "))

    def testverifydeldnsinstance(self):
        command = "show service --service dns"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Service: dns Instance: unittest", command)

    def testverifydnsinstanceplenary(self):
        dir = os.path.join(self.config.get("broker", "plenarydir"),
                           "service", "dns", "unittest")
        self.failIf(os.path.exists(dir),
                    "Plenary directory '%s' still exists" % dir)

    # At this point, pa.ny.na still is still mapped.  del_service
    # should silently remove the mappings.
    def testdelntpinstance(self):
        command = "del service --service ntp --instance pa.ny.na"
        self.noouttest(command.split(" "))

    def testverifydelntpinstance(self):
        command = "show service --service ntp"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Service: ntp Instance: pa.ny.na", command)

    def testdelutsi1instance(self):
        command = "del service --service utsvc --instance utsi1"
        self.noouttest(command.split(" "))

    def testdelutsi2instance(self):
        command = "del service --service utsvc --instance utsi2"
        self.noouttest(command.split(" "))

    def testverifydelutsvcinstance(self):
        command = "show service --service utsvc"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Service: utsvc Instance: utsi1", command)
        self.matchclean(out, "Service: utsvc Instance: utsi2", command)

    def testdelutsvc2(self):
        command = "del service --service utsvc2"
        self.noouttest(command.split(" "))

    def testverifydelutsvc2(self):
        command = "show service --service utsvc2"
        self.notfoundtest(command.split(" "))

    def tetverifydelutsvc2plenary(self):
        dir = os.path.join(self.config.get("broker", "plenarydir"),
                           "service", "utsvc2")
        self.failIf(os.path.exists(dir),
                    "Plenary directory '%s' still exists" % dir)

    def testdelunmappedservice(self):
        command = "del service --service unmapped --instance instance1"
        self.noouttest(command.split(" "))

    def testverifydelunmappedservice(self):
        command = "show service --service unmapped"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Service: unmapped Instance: instance1", command)

    def testdelesxmanagement(self):
        command = "del service --service esx_management_server --instance ut.a"
        self.noouttest(command.split(" "))
        command = "del service --service esx_management_server --instance ut.b"
        self.noouttest(command.split(" "))
        command = "del service --service esx_management_server --instance np"
        self.noouttest(command.split(" "))
        command = "del service --service esx_management_server"
        self.noouttest(command.split(" "))

    def testverifydelesxmanagement(self):
        command = "show service --service esx_management_server"
        self.notfoundtest(command.split(" "))

    def testdelvmseasoning(self):
        command = "del service --service vmseasoning --instance salt"
        self.noouttest(command.split(" "))
        command = "del service --service vmseasoning --instance pepper"
        self.noouttest(command.split(" "))
        command = "del service --service vmseasoning --instance sugar"
        self.noouttest(command.split(" "))
        command = "del service --service vmseasoning"
        self.noouttest(command.split(" "))

    def testverifydelvmseasoning(self):
        command = "show service --service vmseasoning"
        self.notfoundtest(command.split(" "))

    def testdelpollhelper(self):
        service = self.config.get("broker", "poll_helper_service")
        self.noouttest(["del", "service", "--service", service,
                        "--instance", "unittest"])
        self.noouttest(["del", "service", "--service", service])

    def testdelecservice(self):
        command = "del service --service support-group --instance ec-service"
        self.noouttest(command.split(" "))

    def testdelvcenterservices(self):
        command = ["del", "service", "--service", "vcenter", "--instance", "ut"]
        self.noouttest(command)

        command = ["del", "service", "--service", "vcenter", "--instance", "np"]
        self.noouttest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelService)
    unittest.TextTestRunner(verbosity=2).run(suite)
