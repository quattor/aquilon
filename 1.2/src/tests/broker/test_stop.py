#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Test module for stopping the broker."""

import os
import sys
import unittest
import signal

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from aquilon.config import Config


class TestBrokerStop(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def teststop(self):
        config = Config()
        pidfile = os.path.join(config.get("broker", "rundir"), "aqd.pid")
        self.assert_(os.path.exists(pidfile))
        f = file(pidfile)
        pid = f.readline()
        self.assertNotEqual(pid, "")
        f.close()
        pid = int(pid)
        os.kill(pid, signal.SIGTERM)
        # FIXME verify...


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBrokerStop)
    unittest.TextTestRunner(verbosity=2).run(suite)

