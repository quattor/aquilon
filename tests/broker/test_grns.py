#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011  Contributor
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
"""Module for testing GRN support."""

import os
import sys
import unittest
from subprocess import Popen, PIPE

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestGrns(TestBrokerCommand):
    
    def test_100_add_test1(self):
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
        command = ["add", "grn", "--grn", "grn:/ms/test2", "--eon_id", "123456789"]
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
        self.matchoutput(err, "Added 1, updated 1, deleted 1 GRNs.", command)

    def test_210_verify_test1_renamed(self):
        command = ["show", "grn", "--eon_id", "1"]
        out = self.commandtest(command)
        self.matchoutput(out, "GRN: grn:/ms/ei/aquilon", command)
        self.matchoutput(out, "EON ID: 1", command)
        self.matchoutput(out, "Disabled: True", command)

    def test_211_verify_aqd(self):
        command = ["show", "grn", "--grn", "grn:/ms/ei/aquilon/aqd"]
        out = self.commandtest(command)
        self.matchoutput(out, "EON ID: 2", command)
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


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestGrns)
    unittest.TextTestRunner(verbosity=2).run(suite)
