#!/ms/dist/python/PROJ/core/2.5.0/bin/python
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
    # it should now be set to q.ln.ms.com.
    def testreconfigureunittest02(self):
        self.noouttest(["reconfigure",
            "--hostname", "unittest02.one-nyp.ms.com"])

    def testverifycatunittest02(self):
        command = "cat --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
            """'/hardware' = create('machine/americas/ut/ut3/ut3c5n10');""",
            command)
        self.matchoutput(out,
            """'/system/network/interfaces/eth0' = nlist('ip', '%s', 'netmask', '%s', 'broadcast', '%s', 'gateway', '%s', 'bootproto', 'dhcp');""" % (self.hostip0, self.netmask0, self.broadcast0, self.gateway0),
            command)
        self.matchoutput(out,
            """include { 'archetype/base' };""",
            command)
        self.matchoutput(out,
            """include { 'os/linux/4.0.1-x86_64/config' };""",
            command)
        self.matchoutput(out,
            """include { 'service/afs/q.ln.ms.com/client/config' };""",
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
            """'/system/network/interfaces/eth0' = nlist('ip', '%s', 'netmask', '%s', 'broadcast', '%s', 'gateway', '%s', 'bootproto', 'dhcp');""" % (self.hostip2, self.netmask2, self.broadcast2, self.gateway2),
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


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestReconfigure)
    unittest.TextTestRunner(verbosity=2).run(suite)

