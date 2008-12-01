#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the poll tor_switch command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestPollTorSwitch(TestBrokerCommand):

    def testpollnp06bals03(self):
        self.noouttest(["poll", "tor_switch",
                        "--tor_switch", "np06bals03.ms.com"])

    # Tests re-polling np06bals03 and polls np06fals01
    def testpollnp7(self):
        self.noouttest(["poll", "tor_switch", "--rack", "np7"])

    def testverifypollnp06bals03(self):
        command = "show tor_switch --tor_switch np06bals03.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Port 17: 00:30:48:66:3a:62", command)
        self.matchoutput(out, "Port 2: 00:1f:29:c4:39:ba", command)
        self.matchoutput(out, "Port 22: 00:30:48:66:38:e6", command)
        self.matchoutput(out, "Port 4: 00:1f:29:c4:29:ca", command)
        self.matchoutput(out, "Port 5: 00:1f:29:68:53:ca", command)
        self.matchoutput(out, "Port 27: 00:30:48:66:3a:28", command)
        self.matchoutput(out, "Port 20: 00:30:48:66:38:da", command)
        self.matchoutput(out, "Port 39: 00:30:48:98:4d:a3", command)
        self.matchoutput(out, "Port 24: 00:30:48:66:3a:2a", command)
        self.matchoutput(out, "Port 14: 00:1f:29:c4:39:12", command)
        self.matchoutput(out, "Port 3: 00:1f:29:c4:09:ee", command)
        self.matchoutput(out, "Port 49: 00:1a:6c:9e:e3:1e", command)
        self.matchoutput(out, "Port 21: 00:30:48:66:3a:2e", command)
        self.matchoutput(out, "Port 11: 00:1f:29:68:93:e0", command)
        self.matchoutput(out, "Port 31: 00:30:48:98:4d:0a", command)
        self.matchoutput(out, "Port 7: 00:1f:29:c4:19:d0", command)
        self.matchoutput(out, "Port 8: 00:1f:29:c4:59:b0", command)
        self.matchoutput(out, "Port 12: 00:1f:29:c4:19:f2", command)
        self.matchoutput(out, "Port 50: 00:1d:71:73:55:40", command)
        self.matchoutput(out, "Port 40: 00:30:48:98:4d:cc", command)
        self.matchoutput(out, "Port 34: 00:30:48:98:4d:83", command)
        self.matchoutput(out, "Port 50: 00:1a:6c:9e:de:8e", command)
        self.matchoutput(out, "Port 29: 00:30:48:98:4d:5b", command)
        self.matchoutput(out, "Port 10: 00:1f:29:c4:39:14", command)
        self.matchoutput(out, "Port 37: 00:30:48:98:4d:96", command)
        self.matchoutput(out, "Port 49: 00:1d:71:73:53:80", command)
        self.matchoutput(out, "Port 33: 00:30:48:98:4d:97", command)
        self.matchoutput(out, "Port 36: 00:30:48:98:4d:98", command)
        self.matchoutput(out, "Port 49: 00:00:0c:07:ac:01", command)
        self.matchoutput(out, "Port 9: 00:1f:29:c4:29:6a", command)
        self.matchoutput(out, "Port 35: 00:30:48:98:4d:8a", command)
        self.matchoutput(out, "Port 50: 00:00:0c:07:ac:02", command)
        self.matchoutput(out, "Port 32: 00:30:48:98:4d:8b", command)
        self.matchoutput(out, "Port 28: 00:30:48:66:3a:22", command)
        self.matchoutput(out, "Port 18: 00:30:48:66:3a:36", command)
        self.matchoutput(out, "Port 19: 00:30:48:66:3a:46", command)
        self.matchoutput(out, "Port 16: 00:1f:29:68:83:4c", command)
        self.matchoutput(out, "Port 25: 00:30:48:66:3a:38", command)
        self.matchoutput(out, "Port 15: 00:1f:29:c4:59:fe", command)
        self.matchoutput(out, "Port 30: 00:30:48:98:4d:c6", command)
        self.matchoutput(out, "Port 6: 00:1f:29:68:63:ec", command)
        self.matchoutput(out, "Port 23: 00:30:48:66:3a:60", command)

    def testverifypollnp06fals01(self):
        command = "show tor_switch --tor_switch np06fals01.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Port 49: 00:15:2c:1f:40:00", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddTorSwitch)
    unittest.TextTestRunner(verbosity=2).run(suite)

