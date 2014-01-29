#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Module for testing the add os command."""


if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestAddOS(TestBrokerCommand):

    def testaddexisting(self):
        command = "add os --archetype aquilon --osname linux --osversion 5.0.1-x86_64"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Operating System linux, version 5.0.1-x86_64, "
                         "archetype aquilon already exists.",
                         command)

    def testadd60(self):
        command = "add os --archetype aquilon --osname linux --osversion 6.0-x86_64"
        self.noouttest(command.split(" "))

    def testaddbadname(self):
        command = "add os --archetype aquilon --osname oops@! --osversion 1.0"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "'oops@!' is not a valid value for --osname.",
                         command)

    def testaddbadversion(self):
        command = "add os --archetype aquilon --osname newos --osversion oops@!"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "'oops@!' is not a valid value for --osversion.",
                         command)

    def testaddutos(self):
        command = "add os --archetype utarchetype1 --osname utos --osversion 1.0"
        self.noouttest(command.split(" "))

    def testaddutos2(self):
        command = "add os --archetype utarchetype3 --osname utos2 --osversion 1.0"
        self.noouttest(command.split(" "))

    def testaddutappos(self):
        command = "add os --archetype utappliance --osname utos --osversion 1.0"
        self.noouttest(command.split(" "))

    def testverifyutos(self):
        command = "show os --archetype utarchetype1 --osname utos --osversion 1.0"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Operating System: utos", command)
        self.matchoutput(out, "Version: 1.0", command)
        self.matchoutput(out, "Archetype: utarchetype1", command)
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
        self.matchoutput(out, "Operating System: utos", command)
        self.matchclean(out, "linux", command)

    def testverifyversonly(self):
        command = "show os --osversion 1.0 --archetype utarchetype1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Version: 1.0", command)
        self.matchclean(out, "linux", command)

    def testverifyall(self):
        command = "show os --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Operating System: utos", command)
        self.matchoutput(out, "Operating System: linux", command)
        self.matchoutput(out, "Archetype: utarchetype1", command)
        self.matchoutput(out, "Archetype: aquilon", command)

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
