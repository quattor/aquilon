#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the make aquilon command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestMakeAquilon(TestBrokerCommand):

    def testmakeaquilon02(self):
        self.noouttest(["make", "aquilon",
            "--hostname", "aquilon02.one-nyp.ms.com",
            "--personality", "ms/fid/spg/ice", "--os", "linux/4.0.1-x86_64"])
        self.assert_(os.path.exists(os.path.join(
            self.config.get("broker", "hostsdir"),
            "aquilon02.one-nyp.ms.com.tpl")))
        self.assert_(os.path.exists(os.path.join(
            self.config.get("broker", "depsdir"),
            "aquilon02.one-nyp.ms.com.xml.dep")))
        self.assert_(os.path.exists(os.path.join(
            self.config.get("broker", "profilesdir"),
            "aquilon02.one-nyp.ms.com.xml")))

    def testverifycataquilon02(self):
        command = "cat --hostname aquilon02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
            """"/hardware" = create("machine/americas/np/np3/np3c5n10");""",
            command)
        self.matchoutput(out,
            """"/system/network/interfaces/eth0" = nlist("ip", "172.31.73.14", "netmask", "255.255.255.128", "broadcast", "172.31.73.127", "gateway", "172.31.73.1", "bootproto", "dhcp");""",
            command)
        self.matchoutput(out,
            """include { "archetype/base" };""",
            command)
        self.matchoutput(out,
            """include { "os/linux/4.0.1-x86_64/config" };""",
            command)
        self.matchoutput(out,
            """include { "service/afs/q.ny.ms.com/client/config" };""",
            command)
        self.matchoutput(out,
            """include { "service/bootserver/np.test/client/config" };""",
            command)
        self.matchoutput(out,
            """include { "service/dns/nyinfratest/client/config" };""",
            command)
        self.matchoutput(out,
            """include { "service/ntp/pa.ny.na/client/config" };""",
            command)
        self.matchoutput(out,
            """include { "personality/ms/fid/spg/ice/config" };""",
            command)
        self.matchoutput(out,
            """include { "archetype/final" };""",
            command)

    def testmakeaquilon00(self):
        self.noouttest(["make", "aquilon",
            "--hostname", "aquilon00.one-nyp.ms.com",
            "--personality", "ms/fid/spg/ice", "--os", "linux/4.0.1-x86_64"])
        self.assert_(os.path.exists(os.path.join(
            self.config.get("broker", "hostsdir"),
            "aquilon00.one-nyp.ms.com.tpl")))
        self.assert_(os.path.exists(os.path.join(
            self.config.get("broker", "depsdir"),
            "aquilon00.one-nyp.ms.com.xml.dep")))
        self.assert_(os.path.exists(os.path.join(
            self.config.get("broker", "profilesdir"),
            "aquilon00.one-nyp.ms.com.xml")))

    def testverifybindautoafs(self):
        command = "show host --hostname aquilon00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/afs/q.ny.ms.com", command)

    def testverifybindautodns(self):
        command = "show host --hostname aquilon00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/dns/nyinfratest", command)

    def testverifycataquilon00(self):
        command = "cat --hostname aquilon00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
            """"/hardware" = create("machine/americas/np/np3/np3c1n3");""",
            command)
        self.matchoutput(out,
            """"/system/network/interfaces/eth0" = nlist("ip", "172.31.64.199", "netmask", "255.255.255.128", "broadcast", "172.31.64.255", "gateway", "172.31.64.129", "bootproto", "dhcp");""",
            command)
        self.matchoutput(out,
            """include { "archetype/base" };""",
            command)
        self.matchoutput(out,
            """include { "os/linux/4.0.1-x86_64/config" };""",
            command)
        self.matchoutput(out,
            """include { "service/afs/q.ny.ms.com/client/config" };""",
            command)
        self.matchoutput(out,
            """include { "service/bootserver/np.test/client/config" };""",
            command)
        self.matchoutput(out,
            """include { "service/dns/nyinfratest/client/config" };""",
            command)
        self.matchoutput(out,
            """include { "service/ntp/pa.ny.na/client/config" };""",
            command)
        self.matchoutput(out,
            """include { "personality/ms/fid/spg/ice/config" };""",
            command)
        self.matchoutput(out,
            """include { "archetype/final" };""",
            command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMakeAquilon)
    unittest.TextTestRunner(verbosity=2).run(suite)

