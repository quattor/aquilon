#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the show service --all command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestShowServiceAll(TestBrokerCommand):

    def testshowserviceall(self):
        command = "show service --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: afs Instance: q.ny.ms.com", command)
        self.matchoutput(out, "Service: afs Instance: q.ln.ms.com", command)
        self.matchoutput(out, "Service: bootserver Instance: np.test", command)
        self.matchoutput(out, "Service: dns Instance: nyinfratest", command)
        self.matchoutput(out, "Service: ntp Instance: pa.ny.na", command)

    def testshowserviceproto(self):
        command = "show service --all --format proto"
        out = self.commandtest(command.split(" "))
        self.parse_srvlist_msg(out)

if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestShowServiceAll)
    unittest.TextTestRunner(verbosity=2).run(suite)

