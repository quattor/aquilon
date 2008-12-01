#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing constraints in commands involving the umask setting."""

import os
import sys
import stat
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestUmaskConstraints(TestBrokerCommand):

    # Check that all of the git commands have left the index as readable
    # by all.
    def testgitindexpermission(self):
        self.assert_(os.stat(os.path.join(
            self.config.get("broker", "kingdir"), ".git", "index")).st_mode
            & stat.S_IROTH)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUmaskConstraints)
    unittest.TextTestRunner(verbosity=2).run(suite)

