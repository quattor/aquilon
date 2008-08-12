#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the del disk command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestDelDisk(TestBrokerCommand):

    def testdelut3c1n3sda(self):
        self.noouttest(["del", "disk", "--machine", "ut3c1n3",
            "--type", "scsi", "--capacity", "68"])

    def testdelut3c1n3sdb(self):
        self.noouttest(["del", "disk", "--machine", "ut3c1n3",
            "--disk", "sdb"])

    # ARG! The Disk info shows up exactly the same in the MachineSpecs.
    # Hard-coding the indent to get around that.
    def testverifydelut3c1n3sda(self):
        command = "show machine --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "\n  Disk: sda 68 GB scsi", command)

    def testverifydelut3c1n3sdb(self):
        command = "show machine --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Disk: sdb", command)

    # This should now list the 34 GB disk that was added previously...
    def testverifycatut3c1n3disk(self):
        command = "cat --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, '"harddisks"', command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelDisk)
    unittest.TextTestRunner(verbosity=2).run(suite)

