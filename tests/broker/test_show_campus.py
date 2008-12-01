#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the show campus command.

Most of the location show commands are tested in their add/del
counterparts.  However, we have chosen (so far) to not implement
those commands for campus.

"""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestShowCampus(TestBrokerCommand):

    def testshowcampusall(self):
        command = "show campus --all"
        out = self.commandtest(command.split(" "))
        # Just a sampling.
        self.matchoutput(out, "Campus: ny", command)
        self.matchoutput(out, "Fullname: New York", command)
        self.matchoutput(out, "Campus: vi", command)
        self.matchoutput(out, "Fullname: Virginia", command)

    def testshowcampusvi(self):
        command = "show campus --name vi"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Campus: vi", command)
        self.matchoutput(out, "Fullname: Virginia", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestShowCampus)
    unittest.TextTestRunner(verbosity=2).run(suite)

