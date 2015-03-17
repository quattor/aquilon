#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014,2015  Contributor
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
"""Module for testing the update campus command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestUpdateCampus(TestBrokerCommand):
    def test_100_update_ta(self):
        self.noouttest(["update_campus", "--campus", "ta",
                        "--fullname", "New test campus",
                        "--comments", "New campus comments"])

    def test_105_verify_update(self):
        command = "show campus --campus ta"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Campus: ta", command)
        self.matchoutput(out, "Fullname: New test campu", command)
        self.matchoutput(out, "Comments: New campus comments", command)

    def test_110_clear_comments(self):
        self.noouttest(["update_campus", "--campus", "ta", "--comments", ""])

    def test_115_verify_clear(self):
        command = "show campus --campus ta"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Comments", command)

    def test_120_set_default_dns_domain(self):
        self.noouttest(["update_campus", "--campus", "ny",
                        "--default_dns_domain", "new-york.ms.com"])

    def test_125_verify_default_dns_domain(self):
        command = ["show_campus", "--campus", "ny"]
        out = self.commandtest(command)
        self.matchoutput(out, "Default DNS Domain: new-york.ms.com", command)

    def test_200_update_nonexistent(self):
        command = ["update_campus", "--campus", "no-such-campus",
                   "--comments", "No such campus"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Campus no-such-campus not found.", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateCampus)
    unittest.TextTestRunner(verbosity=2).run(suite)
