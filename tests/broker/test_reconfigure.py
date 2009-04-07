#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the reconfigure command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestReconfigure(TestBrokerCommand):

    # The unbind test has removed the service bindings for dns,
    # it should now be set again.
    # The rebind test has changed the service bindings for afs,
    # it should now be set to q.ln.ms.com.  The reconfigure will
    # force it *back* to using a correct service map entry, in
    # this case q.ny.ms.com.
    def testreconfigureunittest02(self):
        command = ["reconfigure", "--hostname", "unittest02.one-nyp.ms.com",
                   "--buildstatus", "ready"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "unittest02.one-nyp.ms.com adding binding for "
                         "service afs instance q.ny.ms.com",
                         command)
        self.matchoutput(out,
                         "unittest02.one-nyp.ms.com removing binding for "
                         "service afs instance q.ln.ms.com",
                         command)

    def testverifybuildstatus(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Build Status: ready", command)

    def testverifycatunittest02(self):
        command = "cat --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
            """'/hardware' = create('machine/americas/ut/ut3/ut3c5n10');""",
            command)
        self.matchoutput(out,
            """'/system/network/interfaces/eth0' = nlist('ip', '%s', 'netmask', '%s', 'broadcast', '%s', 'gateway', '%s', 'bootproto', 'static');""" % (self.hostip0, self.netmask0, self.broadcast0, self.gateway0),
            command)
        self.matchoutput(out,
            """include { 'archetype/base' };""",
            command)
        self.matchoutput(out,
            """include { 'os/linux/4.0.1-x86_64/config' };""",
            command)
        self.matchoutput(out,
            """include { 'service/afs/q.ny.ms.com/client/config' };""",
            command)
        self.matchoutput(out,
            """include { 'service/bootserver/np.test/client/config' };""",
            command)
        self.matchoutput(out,
            """include { 'service/dns/nyinfratest/client/config' };""",
            command)
        self.matchoutput(out,
            """include { 'service/ntp/pa.ny.na/client/config' };""",
            command)
        self.matchoutput(out,
            """include { 'personality/compileserver/config' };""",
            command)
        self.matchoutput(out,
            """include { 'archetype/final' };""",
            command)

    # These settings have not changed - the command should still succeed.
    def testreconfigureunittest00(self):
        self.noouttest(["reconfigure",
            "--hostname", "unittest00.one-nyp.ms.com"])

    def testverifycatunittest00(self):
        command = "cat --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
            """'/hardware' = create('machine/americas/ut/ut3/ut3c1n3');""",
            command)
        self.matchoutput(out,
            """'/system/network/interfaces/eth0' = nlist('ip', '%s', 'netmask', '%s', 'broadcast', '%s', 'gateway', '%s', 'bootproto', 'static');""" % (self.hostip2, self.netmask2, self.broadcast2, self.gateway2),
            command)
        # FIXME: Still working this out...
        #self.matchoutput(out,
        #    """'/system/network/interfaces/eth1' = nlist('ip', '%s', 'netmask', '%s', 'broadcast', '%s', 'gateway', '%s', 'bootproto', 'static');""" % (self.hostip3, self.netmask3, self.broadcast3, self.gateway3),
        #    command)
        self.matchoutput(out,
            """include { 'archetype/base' };""",
            command)
        self.matchoutput(out,
            """include { 'os/linux/4.0.1-x86_64/config' };""",
            command)
        self.matchoutput(out,
            """include { 'service/afs/q.ny.ms.com/client/config' };""",
            command)
        self.matchoutput(out,
            """include { 'service/bootserver/np.test/client/config' };""",
            command)
        self.matchoutput(out,
            """include { 'service/dns/nyinfratest/client/config' };""",
            command)
        self.matchoutput(out,
            """include { 'service/ntp/pa.ny.na/client/config' };""",
            command)
        self.matchoutput(out,
            """include { 'personality/compileserver/config' };""",
            command)
        self.matchoutput(out,
            """include { 'archetype/final' };""",
            command)

    def testreconfigurewindowsstatus(self):
        self.noouttest(["reconfigure",
                        "--hostname", "unittest01.one-nyp.ms.com",
                        "--buildstatus", "ready"])

    def testreconfigurewindowsmissingargs(self):
        command = ["reconfigure", "--hostname", "unittest01.one-nyp.ms.com"]
        err = self.badrequesttest(command)
        self.matchoutput(err, "Nothing to do.", command)

    def testreconfigurewindowspersonality(self):
        command = ["reconfigure", "--hostname", "unittest01.one-nyp.ms.com",
                   "--personality", "desktop"]
        self.noouttest(command)

    def testreconfigurewindowsos(self):
        command = ["reconfigure", "--hostname", "unittest01.one-nyp.ms.com",
                   "--os", "linux/4.0.1-x86_64"]
        err = self.badrequesttest(command)
        self.matchoutput(err, "hosts with archetype aquilon", command)

    def testverifyreconfigurewindows(self):
        command = "show host --hostname unittest01.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Hostname: unittest01.one-nyp.ms.com", command)
        self.matchoutput(out, "Archetype: windows", command)
        self.matchoutput(out, "Personality: desktop", command)
        self.matchoutput(out, "Build Status: ready", command)

    def testreconfigureos(self):
        command = ["reconfigure",
                   "--hostname", "aquilon61.aqd-unittest.ms.com",
                   "--os", "linux/5.0-x86_64"]
        self.noouttest(command)

    def testmissingpersonalitytemplate(self):
        command = ["reconfigure",
                   "--hostname", "aquilon62.aqd-unittest.ms.com",
                   "--personality", "badpersonality"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "cannot locate template", command)
        buildfile = os.path.join(self.config.get("broker", "builddir"),
                                 "domains", "unittest", "profiles",
                                 "aquilon62.aqd-unittest.ms.com.tpl")
        results = self.grepcommand(["-l", "badpersonality", buildfile])
        self.failIf(results, "Found bad personality data in plenary "
                             "template for aquilon62.aqd-unittest.ms.com")

    def testkeepbindings(self):
        command = ["reconfigure", "--keepbindings",
                   "--hostname", "aquilon86.aqd-unittest.ms.com",
                   "--personality", "inventory"]
        self.noouttest(command)

    def verifykeepbindings(self):
        for service in ["chooser1", "chooser2", "chooser3"]:
            command = ["search_host", "--service", service,
                       "--hostname", "aquilon86.aqd-unittest.ms.com",
                       "--personality", "inventory"]
            out = self.commandtest(command)
            self.matchoutput(out, "aquilon86.aqd-unittest.ms.com")

    def testremovebindings(self):
        command = ["reconfigure",
                   "--hostname", "aquilon87.aqd-unittest.ms.com",
                   "--personality", "inventory"]
        out = self.commandtest(command)
        self.matchoutput(out, "removing binding for service chooser1", command)
        self.matchoutput(out, "removing binding for service chooser2", command)
        self.matchoutput(out, "removing binding for service chooser3", command)
        self.matchclean(out, "adding binding", command)

    def verifyremovebindings(self):
        for service in ["chooser1", "chooser2", "chooser3"]:
            command = ["search_host", "--service", service,
                       "--hostname", "aquilon87.aqd-unittest.ms.com"]
            self.noouttest(command)

    def testreconfiguredebug(self):
        command = ["reconfigure", "--debug",
                   "--hostname", "aquilon88.aqd-unittest.ms.com",
                   "--personality", "inventory"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "Creating service Chooser", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestReconfigure)
    unittest.TextTestRunner(verbosity=2).run(suite)

