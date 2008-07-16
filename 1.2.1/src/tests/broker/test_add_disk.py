#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the add disk command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestAddDisk(TestBrokerCommand):

    def testaddut3c5n10disk(self):
        self.noouttest(["add", "disk", "--machine", "ut3c5n10",
            "--disk", "sdb", "--type", "scsi", "--capacity", "34"])

    def testverifyaddut3c5n10disk(self):
        command = "show machine --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Disk: sda 68 GB scsi", command)
        self.matchoutput(out, "Disk: sdb 34 GB scsi", command)

    def testverifycatut3c5n10disk(self):
        command = "cat --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                """"harddisks" = nlist("sda", create("hardware/harddisk/generic/scsi", "capacity", 68*GB), "sdb", create("hardware/harddisk/generic/scsi", "capacity", 34*GB));""",
                command)

    def testaddut3c1n3disk(self):
        self.noouttest(["add", "disk", "--machine", "ut3c1n3",
            "--disk", "sdb", "--type", "scsi", "--capacity", "34"])

    def testverifyaddut3c1n3disk(self):
        command = "show machine --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Disk: sda 68 GB scsi", command)
        self.matchoutput(out, "Disk: sdb 34 GB scsi", command)

    def testverifycatut3c1n3disk(self):
        command = "cat --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                """"harddisks" = nlist("sda", create("hardware/harddisk/generic/scsi", "capacity", 68*GB), "sdb", create("hardware/harddisk/generic/scsi", "capacity", 34*GB));""",
                command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddDisk)
    unittest.TextTestRunner(verbosity=2).run(suite)

