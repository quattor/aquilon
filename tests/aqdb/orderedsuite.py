#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
"""
Module for testing the aqdb commands.
"""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from test_rebuild import TestRebuild

class DatabaseTestSuite(unittest.TestSuite):

    def __init__(self, *args, **kwargs):
        unittest.TestSuite.__init__(self, *args, **kwargs)
        self.addTest(unittest.TestLoader().loadTestsFromTestCase(TestRebuild))



if __name__=='__main__':
    suite = DatabaseTestSuite()
    unittest.TextTestRunner(verbosity=2).run(suite)

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon

