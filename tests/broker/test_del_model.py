#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015  Contributor
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
"""Module for testing the del model command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelModel(TestBrokerCommand):

    def test_100_del_uttorswitch(self):
        command = "del model --model uttorswitch --vendor hp"
        self.noouttest(command.split(" "))

    def test_105_verify_uttorswitch(self):
        command = "show model --model uttorswitch"
        self.notfoundtest(command.split(" "))

    def test_106_del_uttorswitch_again(self):
        command = "del model --model uttorswitch --vendor hp"
        self.notfoundtest(command.split(" "))

    def test_110_del_utblade(self):
        command = "del model --model utblade --vendor aurora_vendor"
        self.noouttest(command.split(" "))

    def test_115_verify_utblade(self):
        command = "show model --model utblade"
        self.notfoundtest(command.split(" "))

    def test_120_del_utvirt_inuse(self):
        command = ["del", "model", "--model", "default", "--vendor", "utvirt"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Model utvirt/default is still referenced by "
                         "machine models and cannot be deleted.",
                         command)

    def test_130_del_utmedium(self):
        command = ["del_model", "--model=utmedium", "--vendor=utvendor"]
        self.noouttest(command)

    def test_135_verify_utmedium(self):
        command = "show model --model utmedium"
        self.notfoundtest(command.split(" "))

    def test_140_del_utlarge(self):
        command = ["del_model", "--model=utlarge", "--vendor=utvendor"]
        self.noouttest(command)

    def test_150_delutva(self):
        command = ["del_model", "--model=utva", "--vendor=utvendor"]
        self.noouttest(command)

    def test_160_del_utrackmount(self):
        self.noouttest(["del_model", "--vendor", "utvendor",
                        "--model", "utrackmount"])

    def test_165_del_unusedcpu(self):
        self.noouttest(["del_model", "--vendor", "utvendor",
                        "--model", "unusedcpu"])

    def test_170_del_utcpu(self):
        command = "del model --model utcpu --vendor intel"
        self.noouttest(command.split(" "))

    def test_175_verify_utcpu(self):
        command = "show cpu --cpu utcpu --vendor intel"
        self.notfoundtest(command.split(" "))

    def test_180_del_utcpu_1500(self):
        command = "del model --model utcpu_1500 --vendor intel"
        self.noouttest(command.split(" "))

    def test_185_del_unused(self):
        self.noouttest(["del_model", "--model", "unused", "--vendor", "utvendor"])

    def test_200_del_unknwon_model(self):
        command = ["del_model", "--model", "no-such-cpu", "--vendor", "utvendor"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Model no-such-cpu, vendor utvendor not found.",
                         command)

    def test_200_del_unknown_vendor(self):
        command = ["del_model", "--model", "no-such-cpu",
                   "--vendor", "no-such-vendor"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Vendor no-such-vendor not found.", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelModel)
    unittest.TextTestRunner(verbosity=2).run(suite)
