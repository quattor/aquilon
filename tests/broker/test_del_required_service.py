#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Module for testing the del required service command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelRequiredService(TestBrokerCommand):

    def testdelrequiredafs(self):
        command = "del required service --service afs --archetype aquilon"
        command += " --justification tcm=12345678"
        self.noouttest(command.split(" "))

    def testdelrequiredafsnojustification(self):
        command = "del required service --service afs --archetype aquilon"
        out = self.unauthorizedtest(command.split(" "), auth=True,
                                    msgcheck=False)
        self.matchoutput(out,
                         "Changing the required services of an archetype "
                         "requires --justification.",
                         command)

    def testdelrequirednetmap(self):
        command = ["del_required_service", "--service=netmap",
                   "--personality=eaitools", "--archetype=aquilon"]
        self.noouttest(command)

    def testdelrequiredafsagain(self):
        command = "del required service --service afs --archetype aquilon"
        command += " --justification tcm=12345678"
        self.notfoundtest(command.split(" "))

    def testdelrequireddns(self):
        command = "del required service --service dns --archetype aquilon"
        command += " --justification tcm=12345678"
        self.noouttest(command.split(" "))

    def testdelrequiredaqd(self):
        command = "del required service --service aqd --archetype aquilon"
        command += " --justification tcm=12345678"
        self.noouttest(command.split(" "))

    def testdelrequiredlemon(self):
        command = "del required service --service lemon --archetype aquilon"
        command += " --justification tcm=12345678"
        self.noouttest(command.split(" "))

    def testdelrequiredntp(self):
        command = "del required service --service ntp --archetype aquilon"
        command += " --justification tcm=12345678"
        self.noouttest(command.split(" "))

    def testdelrequiredbootserver(self):
        command = ["del_required_service",
                   "--service=bootserver", "--archetype=aquilon",
                   "--justification", "tcm=12345678"]
        self.noouttest(command)

    def testdelrequiredsupportgroup(self):
        command = ["del_required_service",
                   "--service=support-group", "--archetype=aquilon",
                   "--justification", "tcm=12345678"]
        self.noouttest(command)

    def testverifydelrequiredservices(self):
        command = "show archetype --archetype aquilon"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Service: afs", command)
        self.matchclean(out, "Service: aqd", command)
        self.matchclean(out, "Service: bootserver", command)
        self.matchclean(out, "Service: dns", command)
        self.matchclean(out, "Service: ntp", command)
        self.matchclean(out, "Service: lemon", command)

    def testdelrequiredpersonality(self):
        for service in ["chooser1", "chooser2", "chooser3"]:
            command = ["del_required_service", "--service", service,
                       "--archetype=aquilon", "--personality=unixeng-test"]
            self.noouttest(command)

    def testdelrequiredpersonalityagain(self):
        command = ["del", "required", "service", "--service", "chooser1",
                   "--archetype=aquilon", "--personality=unixeng-test"]
        self.notfoundtest(command)

    def testverifydelrequiredpersonality(self):
        command = ["show_personality", "--archetype=aquilon",
                   "--personality=unixeng-test"]
        out = self.commandtest(command)
        self.matchclean(out, "Service: chooser1", command)
        self.matchclean(out, "Service: chooser2", command)
        self.matchclean(out, "Service: chooser3", command)

    def testdelrequiredbadpersonality(self):
        command = ["del_required_service", "--service", "badservice",
                   "--archetype=aquilon", "--personality=badpersonality2"]
        self.noouttest(command)

    def testverifydelrequiredbadpersonality(self):
        command = ["show_personality", "--archetype=aquilon",
                   "--personality=badpersonality2"]
        out = self.commandtest(command)
        self.matchclean(out, "Service: badservice", command)

    def testdelrequiredvmhost(self):
        command = ["del_required_service",
                   "--service=dns", "--archetype=vmhost",
                   "--justification=tcm=12345678"]
        self.noouttest(command)
        command = ["del_required_service",
                   "--service=ntp", "--archetype=vmhost",
                   "--justification=tcm=12345678"]
        self.noouttest(command)
        command = ["del_required_service",
                   "--service=syslogng", "--archetype=vmhost",
                   "--justification=tcm=12345678"]
        self.noouttest(command)

    def testverifydelrequiredvmhost(self):
        command = "show archetype --archetype vmhost"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Service: afs", command)
        self.matchclean(out, "Service: dns", command)
        self.matchclean(out, "Service: ntp", command)
        self.matchclean(out, "Service: syslogng", command)

    def testdelrequiredesx(self):
        command = ["del_required_service", "--service=esx_management_server",
                   "--archetype=vmhost", "--personality=vulcan-1g-desktop-prod"]
        self.noouttest(command)
        command = ["del_required_service", "--service=esx_management_server",
                   "--archetype=esx_cluster", "--justification", "tcm=12345678"]
        self.noouttest(command)
        command = ["del_required_service", "--service=esx_management_server",
                   "--archetype=vmhost", "--personality=vulcan2-10g-test"]
        self.noouttest(command)
        command = ["del_required_service", "--service=vmseasoning",
                   "--archetype=vmhost", "--personality=vulcan-1g-desktop-prod"]
        self.noouttest(command)

    def testverifydelrequiredesx(self):
        command = ["show_personality",
                   "--archetype=vmhost", "--personality=vulcan-1g-desktop-prod"]
        out = self.commandtest(command)
        self.matchclean(out, "Service: esx_management_server", command)
        self.matchclean(out, "Service: vmseasoning", command)
        command = ["show_personality",
                   "--archetype=esx_cluster"]
        out = self.commandtest(command)
        self.matchclean(out, "Service: esx_management_server", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelRequiredService)
    unittest.TextTestRunner(verbosity=2).run(suite)
