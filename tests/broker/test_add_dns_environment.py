#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2015,2016,2017  Contributor
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
"""Module for testing the add dns environment command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddDnsEnvironment(TestBrokerCommand):

    def test_100_add_utenv(self):
        command = ["add", "dns", "environment", "--dns_environment", "ut-env",
                   "--comments", "Some DNS env comments"] + self.valid_just_tcm
        self.noouttest(command)

    def test_105_show_utenv(self):
        command = ["show", "dns", "environment", "--dns_environment", "ut-env"]
        out = self.commandtest(command)
        self.matchoutput(out, "DNS Environment: ut-env", command)
        self.matchoutput(out, "Comments: Some DNS env comments", command)

    def test_110_add_excx(self):
        command = ["add", "dns", "environment", "--dns_environment", "excx"] + self.valid_just_tcm
        self.noouttest(command)

    def test_200_add_utenv_again(self):
        command = ["add", "dns", "environment", "--dns_environment", "ut-env"] + self.valid_just_tcm
        out = self.badrequesttest(command)
        self.matchoutput(out, "DNS Environment ut-env already exists.", command)

    def test_200_add_badname(self):
        command = ["add", "dns", "environment", "--dns_environment", "<badname>"] + self.valid_just_tcm
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "'<badname>' is not a valid value for DNS environment",
                         command)

    def test_300_show_all(self):
        command = ["show", "dns", "environment", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "DNS Environment: internal", command)
        self.matchoutput(out, "DNS Environment: external", command)
        self.matchoutput(out, "DNS Environment: ut-env", command)
        self.matchoutput(out, "Comments: Some DNS env comments", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddDnsEnvironment)
    unittest.TextTestRunner(verbosity=2).run(suite)
