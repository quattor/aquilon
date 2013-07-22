#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
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
"""Module for testing GRN support."""

if __name__ == "__main__":
    from broker import utils
    utils.import_depends()

import unittest2 as unittest
from broker.brokertest import TestBrokerCommand
from broker.grntest import VerifyGrnsMixin


class TestGrns(VerifyGrnsMixin, TestBrokerCommand):

    def test_100_add_test1(self):
        self.assert_("grn:/ms/test1" not in self.grns)
        self.assert_(1 in self.eon_ids)
        command = ["add", "grn", "--grn", "grn:/ms/test1", "--eon_id", "1",
                   "--disabled"]
        self.noouttest(command)

    def test_101_verify_test1(self):
        command = ["show", "grn", "--eon_id", "1"]
        out = self.commandtest(command)
        self.matchoutput(out, "GRN: grn:/ms/test1", command)
        self.matchoutput(out, "EON ID: 1", command)
        self.matchoutput(out, "Disabled: True", command)

    def test_110_add_test2(self):
        self.assert_("grn:/ms/test2" not in self.grns)
        command = ["add", "grn", "--grn", "grn:/ms/test2",
                   "--eon_id", "123456789"]
        self.noouttest(command)

    def test_111_verify_test2(self):
        command = ["show", "grn", "--grn", "grn:/ms/test2"]
        out = self.commandtest(command)
        self.matchoutput(out, "GRN: grn:/ms/test2", command)
        self.matchoutput(out, "EON ID: 123456789", command)
        self.matchoutput(out, "Disabled: False", command)

    def test_150_update(self):
        command = ["update", "grn", "--grn", "grn:/ms/test1", "--nodisabled",
                   "--rename_to", "grn:/ms/test3"]
        self.noouttest(command)

    def test_151_verify_update(self):
        command = ["show", "grn", "--eon_id", "1"]
        out = self.commandtest(command)
        self.matchoutput(out, "GRN: grn:/ms/test3", command)
        self.matchoutput(out, "EON ID: 1", command)
        self.matchoutput(out, "Disabled: False", command)

    def test_200_refresh(self):
        command = ["refresh", "grns"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "Added 7, updated 1, deleted 1 GRNs.", command)

    def test_210_verify_test1_renamed(self):
        command = ["show", "grn", "--eon_id", "1"]
        out = self.commandtest(command)
        self.matchoutput(out, "GRN: %s" % self.eon_ids[1], command)
        self.matchoutput(out, "EON ID: 1", command)
        self.matchoutput(out, "Disabled: True", command)

    def test_211_verify_aqd(self):
        command = ["show", "grn", "--grn", "grn:/ms/ei/aquilon/aqd"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "EON ID: %s" % self.grns["grn:/ms/ei/aquilon/aqd"],
                         command)
        self.matchoutput(out, "Disabled: False", command)

    def test_212_verify_test2_gone(self):
        command = ["show", "grn", "--grn", "grn:/ms/test2"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "GRN grn:/ms/test2 not found.", command)

    def test_220_show_missing_eonid(self):
        command = ["show", "grn", "--eon_id", "987654321"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "EON ID 987654321 not found.", command)

    def test_300_delete(self):
        command = ["del", "grn", "--grn", "grn:/ms/ei/aquilon/aqd"]
        self.noouttest(command)

    def test_310_verify_delete_grn(self):
        command = ["show", "grn", "--grn", "grn:/ms/ei/aquilon/aqd"]
        self.notfoundtest(command)

    def test_310_verify_delete_eonid(self):
        command = ["show", "grn", "--eon_id",
                   self.grns["grn:/ms/ei/aquilon/aqd"]]
        self.notfoundtest(command)

    def test_320_refresh_again(self):
        command = ["refresh", "grns"]
        out, err = self.successtest(command)
        self.matchoutput(err, "Added 1, updated 0, deleted 0 GRNs.", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestGrns)
    unittest.TextTestRunner(verbosity=2).run(suite)
