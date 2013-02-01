#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012  Contributor
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
"""Module for testing the add os command."""


import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddOS(TestBrokerCommand):

    def testaddexisting(self):
        command = "add os --archetype aquilon --osname linux --osversion 5.0.1-x86_64"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Operating System linux, version 5.0.1-x86_64, "
                         "archetype aquilon already exists.",
                         command)

    def testaddbadname(self):
        command = "add os --archetype aquilon --osname oops@! --osversion 1.0"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "OS name 'oops@!' is not valid", command)

    def testaddbadversion(self):
        command = "add os --archetype aquilon --osname newos --osversion oops@!"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "OS version 'oops@!' is not valid", command)

    def testaddutos(self):
        command = "add os --archetype utarchetype1 --osname utos --osversion 1.0"
        self.noouttest(command.split(" "))

    def testaddutos2(self):
        command = "add os --archetype utarchetype3 --osname utos2 --osversion 1.0"
        self.noouttest(command.split(" "))

    def testverifyutos(self):
        command = "show os --archetype utarchetype1 --osname utos --osversion 1.0"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Operating System: utos", command)
        self.matchoutput(out, "Version: 1.0", command)
        self.matchoutput(out, "Archetype: utarchetype1", command)
        self.matchoutput(out, "Template: utarchetype1/os/utos/1.0", command)
        self.matchclean(out, "linux", command)

    def testverifyutosproto(self):
        command = ["show_os", "--archetype=utarchetype1", "--osname=utos",
                   "--osversion=1.0", "--format=proto"]
        out = self.commandtest(command)
        oslist = self.parse_os_msg(out, 1)
        utos = oslist.operating_systems[0]
        self.assertEqual(utos.archetype.name, "utarchetype1")
        self.assertEqual(utos.name, "utos")
        self.assertEqual(utos.version, "1.0")

    def testverifyosonly(self):
        command = "show os --osname utos --archetype utarchetype1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: utarchetype1/os/utos/1.0", command)
        self.matchclean(out, "linux", command)

    def testverifyversonly(self):
        command = "show os --osversion 1.0 --archetype utarchetype1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: utarchetype1/os/utos/1.0", command)
        self.matchclean(out, "linux", command)

    def testverifyall(self):
        command = "show os --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Operating System: utos", command)
        self.matchoutput(out, "Operating System: linux", command)
        self.matchoutput(out, "Archetype: utarchetype1", command)
        self.matchoutput(out, "Archetype: aquilon", command)
        self.matchoutput(out, "Template: utarchetype1/os/utos/1.0", command)
        self.matchoutput(out, "Template: aquilon/os/linux/5.0.1-x86_64", command)

    def testverifyallproto(self):
        command = "show os --all --format=proto"
        out = self.commandtest(command.split(" "))
        oslist = self.parse_os_msg(out)
        found_rhel5 = False
        found_ut = False
        for os in oslist.operating_systems:
            if os.archetype.name == 'aquilon' and \
               os.name == 'linux' and os.version == '5.0.1-x86_64':
                found_rhel5 = True
            if os.archetype.name == 'utarchetype1' and \
               os.name == 'utos' and os.version == '1.0':
                found_ut = True
        self.assertTrue(found_rhel5,
                        "Missing proto output for aquilon/linux/5.0.1-x86_64")
        self.assertTrue(found_ut,
                        "Missing proto output for utarchetype1/utos/1.0")

    def testshownotfound(self):
        command = "show os --osname os-does-not-exist --osversion foobar --archetype aquilon"
        self.notfoundtest(command.split(" "))

    def testupdateoscomments(self):
        command = ["update_os", "--osname", "windows", "--osversion", "nt61e",
                   "--archetype", "windows",
                   "--comments", "Windows 7 Enterprise (x86)"]
        self.noouttest(command)

    def testverifyoscomments(self):
        command = "show os --archetype windows --osname windows --osversion nt61e"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Comments: Windows 7 Enterprise (x86)", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddOS)
    unittest.TextTestRunner(verbosity=2).run(suite)
