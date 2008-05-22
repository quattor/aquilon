#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the unmap service command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestUnmapService(TestBrokerCommand):

    def testunmapafs(self):
        self.noouttest(["unmap", "service", "--building", "np",
            "--service", "afs", "--instance", "q.ny.ms.com"])

    def testverifyunmapafs(self):
        command = "show map --service afs --instance q.ny.ms.com --building np"
        self.notfoundtest(command.split(" "))

    def testunmapdns(self):
        self.noouttest(["unmap", "service", "--hub", "ny",
            "--service", "dns", "--instance", "nyinfratest"])

    def testverifyunmapdns(self):
        command = "show map --service dns --instance nyinfratest --hub ny"
        self.notfoundtest(command.split(" "))

    def testunmapbootserver(self):
        self.noouttest(["unmap", "service", "--rack", "np3",
            "--service", "bootserver", "--instance", "np.test"])

    def testverifyunmapbootserver(self):
        command = "show map --service bootserver --instance np.test --rack np3"
        self.notfoundtest(command.split(" "))

    def testunmapntp(self):
        self.noouttest(["unmap", "service", "--city", "ny",
            "--service", "ntp", "--instance", "pa.ny.na"])

    def testverifyunmapntp(self):
        command = "show map --service ntp --instance pa.ny.na --city ny"
        self.notfoundtest(command.split(" "))


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUnmapService)
    unittest.TextTestRunner(verbosity=2).run(suite)

