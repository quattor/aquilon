#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the map service command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestMapService(TestBrokerCommand):

    def testmapafs(self):
        self.noouttest(["map", "service", "--building", "ut",
            "--service", "afs", "--instance", "q.ny.ms.com"])

    def testverifymapafs(self):
        command = "show map --service afs --instance q.ny.ms.com --building ut"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                "Service: afs Instance: q.ny.ms.com Map: Building ut", command)

    def testmapdns(self):
        self.noouttest(["map", "service", "--hub", "ny",
            "--service", "dns", "--instance", "nyinfratest"])

    def testverifymapdns(self):
        command = "show map --service dns --instance nyinfratest --hub ny"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                "Service: dns Instance: nyinfratest Map: Hub ny", command)

    def testmapbootserver(self):
        self.noouttest(["map", "service", "--rack", "ut3",
            "--service", "bootserver", "--instance", "np.test"])

    def testverifymapbootserver(self):
        command = "show map --service bootserver --instance np.test --rack ut3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                "Service: bootserver Instance: np.test Map: Rack ut3", command)

    def testmapntp(self):
        self.noouttest(["map", "service", "--city", "ny",
            "--service", "ntp", "--instance", "pa.ny.na"])

    def testverifymapntp(self):
        command = "show map --service ntp --instance pa.ny.na --city ny"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                "Service: ntp Instance: pa.ny.na Map: City ny", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMapService)
    unittest.TextTestRunner(verbosity=2).run(suite)

