#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014,2015  Contributor
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


import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddOS(TestBrokerCommand):
    linux_version_prev = None
    linux_version_curr = None

    @classmethod
    def setUpClass(cls):
        super(TestAddOS, cls).setUpClass()
        cls.linux_version_prev = cls.config.get("unittest",
                                                "linux_version_prev")
        cls.linux_version_curr = cls.config.get("unittest",
                                                "linux_version_curr")

    def test_100_add_aquilon_prev(self):
        self.noouttest(["add_os", "--archetype", "aquilon", "--osname", "linux",
                        "--osversion", self.linux_version_prev])

    def test_105_add_aquilon_new(self):
        self.noouttest(["add_os", "--archetype", "aquilon", "--osname", "linux",
                        "--osversion", self.linux_version_curr])

    def test_110_add_aurora_prev(self):
        self.noouttest(["add_os", "--archetype", "aurora", "--osname", "linux",
                        "--osversion", self.linux_version_prev])

    def test_120_add_utos(self):
        command = "add os --archetype utarchetype1 --osname utos --osversion 1.0"
        self.noouttest(command.split(" "))

    def test_121_show_utos(self):
        command = "show os --archetype utarchetype1 --osname utos --osversion 1.0"
        out = self.commandtest(command.split(" "))
        self.output_equals(out, """
            Operating System: utos
              Version: 1.0
              Archetype: utarchetype1
            """, command)

    def test_121_show_utos_proto(self):
        command = ["show_os", "--archetype=utarchetype1", "--osname=utos",
                   "--osversion=1.0", "--format=proto"]
        utos = self.protobuftest(command, expect=1)[0]
        self.assertEqual(utos.archetype.name, "utarchetype1")
        self.assertEqual(utos.name, "utos")
        self.assertEqual(utos.version, "1.0")

    def test_121_verify_os_only(self):
        command = "show os --osname utos --archetype utarchetype1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Operating System: utos", command)
        self.matchclean(out, "linux", command)

    def test_121_verify_vers_only(self):
        command = "show os --osversion 1.0 --archetype utarchetype1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Version: 1.0", command)
        self.matchclean(out, "linux", command)

    def test_125_add_utos2(self):
        command = "add os --archetype utarchetype3 --osname utos2 --osversion 1.0"
        self.noouttest(command.split(" "))

    def test_130_add_utappos(self):
        command = "add os --archetype utappliance --osname utos --osversion 1.0"
        self.noouttest(command.split(" "))

    def test_140_add_solaris(self):
        self.noouttest(["add_os", "--archetype", "aquilon", "--osname", "solaris",
                        "--osversion", "11.1-x86_64"])

    def test_200_add_existing(self):
        command = ["add_os", "--archetype", "aquilon", "--osname", "linux",
                   "--osversion", self.linux_version_prev]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Operating System linux, version %s, "
                         "archetype aquilon already exists." %
                         self.linux_version_prev,
                         command)

    def test_200_add_bad_name(self):
        command = "add os --archetype aquilon --osname oops@! --osversion 1.0"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "'oops@!' is not a valid value for --osname.",
                         command)

    def test_200_add_bad_version(self):
        command = "add os --archetype aquilon --osname newos --osversion oops@!"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "'oops@!' is not a valid value for --osversion.",
                         command)

    def test_200_show_not_found(self):
        command = "show os --osname os-does-not-exist --osversion foobar --archetype aquilon"
        self.notfoundtest(command.split(" "))

    def test_300_verify_all(self):
        command = "show os --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Operating System: utos", command)
        self.matchoutput(out, "Operating System: linux", command)
        self.matchoutput(out, "Archetype: utarchetype1", command)
        self.matchoutput(out, "Archetype: aquilon", command)

    def test_310_verify_all_proto(self):
        command = "show os --all --format=proto"
        oslist = self.protobuftest(command.split(" "))
        found_aquilon_new = False
        found_ut = False
        for os in oslist:
            if os.archetype.name == 'aquilon' and \
               os.name == 'linux' and os.version == self.linux_version_curr:
                found_aquilon_new = True
            if os.archetype.name == 'utarchetype1' and \
               os.name == 'utos' and os.version == '1.0':
                found_ut = True
        self.assertTrue(found_aquilon_new,
                        "Missing proto output for aquilon/linux/%s" %
                        self.linux_version_curr)
        self.assertTrue(found_ut,
                        "Missing proto output for utarchetype1/utos/1.0")

    def test_400_update_os_comments(self):
        command = ["update_os", "--osname", "windows", "--osversion", "nt61e",
                   "--archetype", "windows",
                   "--comments", "Windows 7 Enterprise (x86)"]
        self.noouttest(command)

    def test_410_verify_os_comments(self):
        command = "show os --archetype windows --osname windows --osversion nt61e"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Comments: Windows 7 Enterprise (x86)", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddOS)
    unittest.TextTestRunner(verbosity=2).run(suite)
