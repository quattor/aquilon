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

services_to_delete = {
    "afs": ["q.ny.ms.com", "afs-by-net", "afs-by-net2", "q.ln.ms.com"],
    "aqd": ["ny-prod"],
    "badservice": [],
    "bootserver": ["one-nyp", "unittest"],
    "dns": ["unittest", "one-nyp"],
    "esx_management_server": ["ut.a", "ut.b", "np"],
    "lemon": ["ny-prod"],
    "netmap": ["netmap-pers", "q.ny.ms.com", "p-q.ny.ms.com"],
    "support-group": ["ec-service"],
    "syslogng": ["ny-prod"],
    "unmapped": ["instance1"],
    "utnotify": ["localhost"],
    "vcenter": ["ut", "np"],
    "vmseasoning": ["salt", "pepper", "sugar"],
}


class TestDelService(TestBrokerCommand):

    def testdelservices(self):
        for service, instances in services_to_delete.items():
            for instance in instances:
                self.noouttest(["del_service", "--service", service,
                                "--instance", instance])

            command = ["show_service", "--service", service]
            out = self.commandtest(command)
            for instance in instances:
                self.matchclean(out, instance, command)

            self.noouttest(["del_service", "--service", service])

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

    def testdelpollhelper(self):
        service = self.config.get("broker", "poll_helper_service")
        self.noouttest(["del", "service", "--service", service,
                        "--instance", "unittest"])
        self.noouttest(["del", "service", "--service", service])


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelService)
    unittest.TextTestRunner(verbosity=2).run(suite)
