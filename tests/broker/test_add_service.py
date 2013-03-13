#!/usr/bin/env python2.6
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
"""Module for testing the add service command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddService(TestBrokerCommand):

    def testaddafsinstance(self):
        command = ["add", "service", "--service", "afs",
                   "--instance", "q.ny.ms.com",
                   "--comments", "Some instance comments"]
        self.noouttest(command)

    def testaddafsbynetinstance(self):
        command = ["add", "service", "--service", "afs",
                   "--instance", "afs-by-net",
                   "--comments", "For network based maps"]
        self.noouttest(command)

    def testaddafsbynetdupinstance(self):
        command = ["add", "service", "--service", "afs",
                   "--instance", "afs-by-net2",
                   "--comments", "afs-by-net duplicate"]
        self.noouttest(command)

    def testaddnetmappersinstances(self):
        command = ["add", "service", "--service", "netmap",
                   "--instance", "q.ny.ms.com",
                   "--comments", "For location based maps"]
        self.noouttest(command)

        command = ["add", "service", "--service", "netmap",
                   "--instance", "p-q.ny.ms.com",
                   "--comments", "For location based maps with personality"]
        self.noouttest(command)

        command = ["add", "service", "--service", "netmap",
                   "--instance", "netmap-pers",
                   "--comments", "For network based maps"]
        self.noouttest(command)

    def testaddduplicateservice(self):
        command = "add service --service afs"
        self.badrequesttest(command.split(" "))

    def testaddduplicateinstance(self):
        command = "add service --service afs --instance q.ny.ms.com"
        self.badrequesttest(command.split(" "))

    def testverifyaddafsinstance(self):
        command = "show service --service afs"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: afs Instance: q.ny.ms.com", command)

    def testverifiyaddafsbynetinstance(self):
        command = "show service --service afs"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: afs Instance: afs-by-net", command)

    def testaddextraafsinstance(self):
        command = "add service --service afs --instance q.ln.ms.com"
        self.noouttest(command.split(" "))

    def testverifyaddextraafsinstance(self):
        command = "show service --service afs"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: afs Instance: q.ln.ms.com", command)
        # Make sure the right object got the comments
        self.matchoutput(out, "    Comments: Some instance comments", command)
        self.searchclean(out, r"^  Comments:", command)

    def testaddbootserver(self):
        """ add service without instance first """
        command = ["add", "service", "--service", "bootserver",
                   "--comments", "Some service comments"]
        self.noouttest(command)

    def testaddbootserverinstance(self):
        command = "add service --service bootserver --instance np.test"
        self.noouttest(command.split(" "))

    def testverifyaddbootserverinstance(self):
        command = "show service --service bootserver"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: bootserver Instance: np.test", command)
        self.searchoutput(out, r"^  Comments: Some service comments", command)

    def testadddnsinstance(self):
        command = "add service --service dns --instance utdnsinstance"
        self.noouttest(command.split(" "))

    def testverifyadddnsinstance(self):
        command = "show service --service dns"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: dns Instance: utdnsinstance", command)

    def testaddntpinstance(self):
        command = "add service --service ntp --instance pa.ny.na"
        self.noouttest(command.split(" "))

    def testverifyaddntpinstance(self):
        command = "show service --service ntp"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: ntp Instance: pa.ny.na", command)

    def testaddaqdinstance(self):
        command = "add service --service aqd --instance ny-prod"
        self.noouttest(command.split(" "))

    def testverifyaddaqdinstance(self):
        command = "show service --service aqd"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: aqd Instance: ny-prod", command)

    def testaddlemoninstance(self):
        command = "add service --service lemon --instance ny-prod"
        self.noouttest(command.split(" "))

    def testverifyaddlemoninstance(self):
        command = "show service --service lemon"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: lemon Instance: ny-prod", command)

    def testaddsyslognginstance(self):
        command = "add service --service syslogng --instance ny-prod"
        self.noouttest(command.split(" "))

    def testverifyaddsyslognginstance(self):
        command = "show service --service syslogng"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: syslogng Instance: ny-prod", command)

    def testaddutsi1instance(self):
        command = "add service --service utsvc --instance utsi1"
        self.noouttest(command.split(" "))

    def testcatutsvcserverdefault(self):
        command = ["cat", "--service", "utsvc", "--server", "--default"]
        out = self.commandtest(command)
        self.matchoutput(out, "template service/utsvc/server/config;", command)

    def testcatutsi1(self):
        command = "cat --service utsvc --instance utsi1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi1/config;",
                         command)
        self.matchoutput(out, 'include { "servicedata/utsvc/config" };',
                         command)
        self.matchoutput(out, '"instance" = "utsi1";', command)
        self.searchoutput(out, r'"servers" = list\(\s*\);', command)

    def testcatutsi1default(self):
        command = "cat --service utsvc --instance utsi1 --default"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "template service/utsvc/utsi1/client/config;",
                         command)
        self.matchoutput(out,
                         '"/system/services/utsvc" = create("servicedata/utsvc/utsi1/config");',
                         command)
        self.matchoutput(out, 'include { "service/utsvc/client/config" };',
                         command)

    def testcatutsi1uiserver(self):
        command = "cat --service utsvc --instance utsi1 --server"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi1/srvconfig;",
                         command)
        self.matchoutput(out, '"instance" = "utsi1";', command)
        self.searchoutput(out, r'"clients" = list\(\s*\);', command)

    def testcatutsi1uiserverdefault(self):
        command = "cat --service utsvc --instance utsi1 --server --default"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "template service/utsvc/utsi1/server/config;",
                         command)
        self.matchoutput(out,
                         '"/system/provides/utsvc" = create("servicedata/utsvc/utsi1/srvconfig");',
                         command)
        self.matchoutput(out,
                         'include { "service/utsvc/server/config" };',
                         command)

    def testaddutsi2instance(self):
        command = "add service --service utsvc --instance utsi2"
        self.noouttest(command.split(" "))

    def testcatutsi2(self):
        command = "cat --service utsvc --instance utsi2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi2/config;",
                         command)
        self.matchoutput(out, 'include { "servicedata/utsvc/config" };',
                         command)
        self.matchoutput(out, '"instance" = "utsi2";', command)
        self.searchoutput(out, r'"servers" = list\(\s*\);', command)

    def testcatutsi2default(self):
        command = "cat --service utsvc --instance utsi2 --default"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "template service/utsvc/utsi2/client/config;",
                         command)
        self.matchoutput(out,
                         '"/system/services/utsvc" = create("servicedata/utsvc/utsi2/config");',
                         command)
        self.matchoutput(out, 'include { "service/utsvc/client/config" };',
                         command)

    def testcatutsvc(self):
        command = "cat --service utsvc"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "structure template servicedata/utsvc/config;",
                         command)

    def testcatutsvcdefault(self):
        command = "cat --service utsvc --default"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "template service/utsvc/client/config;", command)

    def testverifyaddutsvcinstances(self):
        command = "show service --service utsvc"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: utsvc Instance: utsi1", command)
        self.matchoutput(out, "Service: utsvc Instance: utsi2", command)

    def testaddutsvc2(self):
        command = "add service --service utsvc2"
        self.noouttest(command.split(" "))

    def testcatutsvc2(self):
        command = "cat --service utsvc2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "structure template servicedata/utsvc2/config;",
                         command)

    def testcatutsvc2default(self):
        command = "cat --service utsvc2 --default"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "template service/utsvc2/client/config;",
                         command)

    def testverifyutsvc2(self):
        command = "show service --service utsvc2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: utsvc2", command)

    def testaddchooser1(self):
        command = "add service --service chooser1"
        self.noouttest(command.split(" "))

    def testaddchooser2(self):
        command = "add service --service chooser2"
        self.noouttest(command.split(" "))

    def testaddchooser3(self):
        command = "add service --service chooser3"
        self.noouttest(command.split(" "))

    # Testing server affinity - ut.a will be available to all
    # three of chooser[123], but it will be the only instance
    # (with corresponding server) in common to all three.
    def testaddchooser1uta(self):
        command = "add service --service chooser1 --instance ut.a"
        self.noouttest(command.split(" "))

    def testaddchooser1utb(self):
        command = "add service --service chooser1 --instance ut.b"
        self.noouttest(command.split(" "))

    def testaddchooser1utc(self):
        command = "add service --service chooser1 --instance ut.c"
        self.noouttest(command.split(" "))

    # Skipping ut.b for chooser2
    def testaddchooser2uta(self):
        command = "add service --service chooser2 --instance ut.a"
        self.noouttest(command.split(" "))

    def testaddchooser2utc(self):
        command = "add service --service chooser2 --instance ut.c"
        self.noouttest(command.split(" "))

    # Skipping ut.c for chooser3
    def testaddchooser3uta(self):
        command = "add service --service chooser3 --instance ut.a"
        self.noouttest(command.split(" "))

    def testaddchooser3utb(self):
        command = "add service --service chooser3 --instance ut.b"
        self.noouttest(command.split(" "))

    def testaddbadservice(self):
        # This service will not have any instances...
        command = "add service --service badservice"
        self.noouttest(command.split(" "))

    def testverifyaddbadservice(self):
        command = "show service --service badservice"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: badservice", command)

    def testaddunmappedservice(self):
        # These service instances will not have any maps...
        command = "add service --service unmapped --instance instance1"
        self.noouttest(command.split(" "))

    def testverifyunmappedservice(self):
        command = "show service --service unmapped"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: unmapped", command)

    def testaddesxmanagement(self):
        command = "add service --service esx_management_server --instance ut.a"
        self.noouttest(command.split(" "))
        command = "add service --service esx_management_server --instance ut.b"
        self.noouttest(command.split(" "))
        command = "add service --service esx_management_server --instance np"
        self.noouttest(command.split(" "))

    def testverifyesxmanagement(self):
        command = "show service --service esx_management_server"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: esx_management_server", command)
        self.matchoutput(out, "Service: esx_management_server Instance: ut.a",
                         command)
        self.matchoutput(out, "Service: esx_management_server Instance: ut.b",
                         command)
        self.matchoutput(out, "Service: esx_management_server Instance: np",
                         command)

    def testaddvmseasoning(self):
        command = "add service --service vmseasoning --instance salt"
        self.noouttest(command.split(" "))
        command = "add service --service vmseasoning --instance pepper"
        self.noouttest(command.split(" "))
        command = "add service --service vmseasoning --instance sugar"
        self.noouttest(command.split(" "))

    def testverifyvmseasoning(self):
        command = "show service --service vmseasoning"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: vmseasoning", command)
        self.matchoutput(out, "Service: vmseasoning Instance: salt", command)
        self.matchoutput(out, "Service: vmseasoning Instance: pepper", command)
        self.matchclean(out, "Disk Count", command)

    def testaddnotify(self):
        self.noouttest(["add", "service", "--service", "utnotify"])
        self.noouttest(["add", "service", "--service", "utnotify",
                        "--instance", "localhost"])

    def testaddpollhelper(self):
        service = self.config.get("broker", "poll_helper_service")
        self.noouttest(["add", "service", "--service", service])
        self.noouttest(["add", "service", "--service", service,
                        "--instance", "unittest"])


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddService)
    unittest.TextTestRunner(verbosity=2).run(suite)
