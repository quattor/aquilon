#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Module for testing the add disk command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddDisk(TestBrokerCommand):

    def testaddut3c5n10disk(self):
        self.noouttest(["add", "disk", "--machine", "ut3c5n10",
            "--disk", "sdb", "--controller", "scsi", "--size", "34"])

    def testfailaddut3c5n10disk(self):
        command = ["add_disk", "--machine=ut3c5n10", "--disk=sdc",
                   "--controller=controller-does-not-exist", "--size=34"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "controller-does-not-exist is not a valid "
                         "controller type",
                         command)

    def testverifyaddut3c5n10disk(self):
        command = "show machine --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Disk: sda 68 GB scsi", command)
        self.matchoutput(out, "Disk: sdb 34 GB scsi", command)

    def testverifycatut3c5n10disk(self):
        command = "cat --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r'"harddisks" = nlist\(\s*"sda", '
                          r'create\("hardware/harddisk/generic/scsi",\s*'
                          r'"capacity", 68\*GB\s*\),\s*'
                          r'"sdb", create\("hardware/harddisk/generic/scsi",\s*'
                          r'"capacity", 34\*GB\s*\)\s*\);',
                          command)

    def testaddut3c1n3disk(self):
        # Use the deprecated option names here
        self.noouttest(["add", "disk", "--machine", "ut3c1n3",
            "--disk", "c0d0", "--type", "cciss", "--capacity", "34"])

    def testverifyaddut3c1n3disk(self):
        command = "show machine --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Disk: sda 68 GB scsi", command)
        self.matchoutput(out, "Disk: c0d0 34 GB cciss", command)

    def testverifycatut3c1n3disk(self):
        command = "cat --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r'"harddisks" = nlist\(\s*escape\("cciss/c0d0"\), '
                          r'create\("hardware/harddisk/generic/cciss",\s*'
                          r'"capacity", 34\*GB\s*\),\s*'
                          r'"sda", create\("hardware/harddisk/generic/scsi",\s*'
                          r'"capacity", 68\*GB\s*\)\s*\);',
                          command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddDisk)
    unittest.TextTestRunner(verbosity=2).run(suite)
