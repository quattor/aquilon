#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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
"""Module for testing the add service command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand

# taken from test_add_service.py
class TestAddShare(TestBrokerCommand):
    def testaddnasshares(self):
        # Creates shares test_share_1 through test_share_9
        for i in range(1, 10):
            self.noouttest(["add_service", "--service=nas_disk_share",
                            "--instance=test_share_%s" % i])

    def testadd10gigshares(self):
        for i in range(5, 11):
            self.noouttest(["add_service", "--service=nas_disk_share",
                            "--instance=utecl%d_share" % i])

    def testaddhashares(self):
        for i in range(11, 13):
            self.noouttest(["add_service", "--service=nas_disk_share",
                            "--instance=utecl%d_share" % i])
            self.noouttest(["add_service", "--service=nas_disk_share",
                            "--instance=npecl%d_share" % i])

    def testaddmgdshares(self):
        for i in range(13, 15):
            self.noouttest(["add_nas_disk_share", "--share=utecl%d_share" % i,
                            "--manager", "resourcepool"])

    def testverifydiskcount(self):
        command = ["show_service", "--service=nas_disk_share",
                   "--instance=test_share_1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Disk Count: 0", command)

    def testverifyshowshare(self):
        command = ["show_nas_disk_share", "--share=test_share_1"]
        out = self.commandtest(command)
        self.matchoutput(out, "NAS Disk Share: test_share_1", command)
        self.matchoutput(out, "Server: lnn30f1", command)
        self.matchoutput(out, "Mountpoint: /vol/lnn30f1v1/test_share_1",
                         command)
        self.matchoutput(out, "Disk Count: 0", command)
        self.matchoutput(out, "Maximum Disk Count: Default (Unlimited)",
                         command)
        self.matchoutput(out, "Machine Count: 0", command)
        self.matchclean(out, "Comments", command)
        self.matchclean(out, "NAS Disk Share: test_share_2", command)

    def testverifyshowshareall(self):
        command = ["show_nas_disk_share", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "NAS Disk Share: test_share_1", command)
        self.matchoutput(out, "NAS Disk Share: test_share_2", command)
        self.matchoutput(out, "Server: lnn30f1", command)
        self.matchoutput(out, "Mountpoint: /vol/lnn30f1v1/test_share_1",
                         command)
        self.matchoutput(out, "Disk Count: 0", command)
        self.matchoutput(out, "Machine Count: 0", command)

    # TODO remove this in next commit
    def testcatnasinfo(self):
        command = ["cat", "--nasinfo=test_share_1"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "structure template service/nas_disk_share/"
                         "test_share_1/client/nasinfo",
                         command)
        self.matchoutput(out, '"sharename" = "test_share_1";', command)
        self.matchoutput(out, '"server" = "lnn30f1";', command)
        self.matchoutput(out, '"mountpoint" = "/vol/lnn30f1v1/test_share_1";',
                         command)

    def testfailaddnasshare(self):
        command = ["add_service", "--service=nas_disk_share",
                   "--instance=share-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Share share-does-not-exist cannot be found "
                         "in NAS maps.",
                         command)



if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddShare)
    unittest.TextTestRunner(verbosity=2).run(suite)

