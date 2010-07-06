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
"""Module for testing the unmap service command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUnmapService(TestBrokerCommand):

    def testunmapafs(self):
        self.noouttest(["unmap", "service", "--building", "ut",
                        "--service", "afs", "--instance", "q.ny.ms.com"])

    def testverifyunmapafs(self):
        command = ["show_map",
                   "--service=afs", "--instance=q.ny.ms.com", "--building=ut"]
        self.notfoundtest(command)

    def testunmapdns(self):
        self.noouttest(["unmap", "service", "--hub", "ny",
                        "--service", "dns", "--instance", "utdnsinstance"])

    def testverifyunmapdns(self):
        command = ["show_map",
                   "--service=dns", "--instance=utdnsinstance", "--hub=ny"]
        self.notfoundtest(command)

    def testunmapaqd(self):
        self.noouttest(["unmap", "service", "--campus", "ny",
                        "--service", "aqd", "--instance", "ny-prod"])

    def testverifyunmapaqd(self):
        command = ["show_map",
                   "--service=aqd", "--instance=ny-prod", "--campus=ny"]
        self.notfoundtest(command)

    def testunmaplemon(self):
        self.noouttest(["unmap", "service", "--campus", "ny",
                        "--service", "lemon", "--instance", "ny-prod"])

    def testverifyunmaplemon(self):
        command = ["show_map",
                   "--service=lemon", "--instance=ny-prod", "--campus=ny"]
        self.notfoundtest(command)

    def testunmapbootserver(self):
        self.noouttest(["unmap", "service", "--building", "ut",
                        "--service", "bootserver", "--instance", "np.test"])

    def testverifyunmapbootserver(self):
        command = ["show_map", "--service=bootserver", "--instance=np.test",
                   "--building=ut"]
        self.notfoundtest(command)

    # Not unmap'ing ntp to test that the service instance is still
    # deleted correctly.  (Deleting the service instance will blow
    # away any maps.)
   #def testunmapntp(self):
   #    self.noouttest(["unmap", "service", "--city", "ny",
   #                    "--service", "ntp", "--instance", "pa.ny.na",
   #                    "--archetype", "aquilon"])

   #def testverifyunmapntp(self):
   #    command = ["show_map", "--archetype=aquilon",
   #               "--service=ntp", "--instance=pa.ny.na", "--city=ny"]
   #    self.notfoundtest(command)

    def testunmaputsi1(self):
        self.noouttest(["unmap", "service", "--building", "ut",
                        "--service", "utsvc", "--instance", "utsi1"])

    def testverifyunmaputsi1(self):
        command = ["show_map",
                   "--service=utsvc", "--instance=utsi1", "--building=ut"]
        self.notfoundtest(command)

    def testunmaputsi2(self):
        self.noouttest(["unmap", "service", "--building", "ut",
                        "--service", "utsvc", "--instance", "utsi2"])

    def testverifyunmaputsi2(self):
        command = ["show_map",
                   "--service=utsvc", "--instance=utsi2", "--building=ut"]
        self.notfoundtest(command)

    def testunmapchooser(self):
        for service in ["chooser1", "chooser2", "chooser3"]:
            for n in ['a', 'b', 'c']:
                if service == 'chooser2' and n == 'b':
                    continue
                if service == 'chooser3' and n == 'c':
                    continue
                instance = "ut.%s" % n
                self.noouttest(["unmap", "service", "--building", "ut",
                                "--service", service, "--instance", instance])

    def testunmapwithpersona(self):
        self.noouttest(["unmap", "service", "--organization", "ms", "--service", "utsvc",
                        "--instance", "utsi2", "--archetype", "aquilon",
                        "--personality", "lemon-collector-oracle"])

    def testverifyunmapwithpersona(self):
        command = "show map --archetype aquilon --personality lemon-collector-oracle --service utsvc"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "", command)

    # TODO: If/when there is another mapped personality, explicitly skip
    # the unmap operation to test that del_service automatically removes
    # the mapping.

    def testunmapesx(self):
        self.noouttest(["unmap", "service", "--building", "ut",
                        "--service", "esx_management_server",
                        "--instance", "ut.a", "--archetype", "vmhost",
                        "--personality", "esx_desktop"])
        self.noouttest(["unmap", "service", "--building", "ut",
                        "--service", "esx_management_server",
                        "--instance", "ut.b", "--archetype", "vmhost",
                        "--personality", "esx_desktop"])
        self.noouttest(["unmap", "service", "--building", "ut",
                        "--service", "vmseasoning", "--instance", "salt",
                        "--archetype", "vmhost",
                        "--personality", "esx_desktop"])
        self.noouttest(["unmap", "service", "--building", "ut",
                        "--service", "vmseasoning", "--instance", "pepper",
                        "--archetype", "vmhost",
                        "--personality", "esx_desktop"])

    def testverifyunmapesx(self):
        command = ["show_map", "--archetype=vmhost",
                   "--personality=esx_desktop", "--building=ut"]
        out = self.commandtest(command)
        self.matchclean(out, "Service: esx_management_server Instance: ut.a ",
                        command)
        self.matchclean(out, "Service: esx_management_server Instance: ut.b ",
                        command)
        self.matchclean(out, "Service: vmseasoning Instance: salt", command)
        self.matchclean(out, "Service: vmseasoning Instance: pepper", command)

    def testunmapwindowsfail(self):
        command = ["unmap", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--archetype", "windows"]
        out = self.badoptiontest(command)
        self.matchoutput(out, "Not all mandatory options specified!", command)

    def testunmapgenericfail(self):
        command = ["unmap", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--personality", "generic"]
        out = self.badoptiontest(command)
        self.matchoutput(out, "Not all mandatory options specified!", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUnmapService)
    unittest.TextTestRunner(verbosity=2).run(suite)
