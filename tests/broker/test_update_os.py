#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2017  Contributor
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

from brokertest import TestBrokerCommand


class TestUpdateOS(TestBrokerCommand):
    def test_100_check_host_for_cm(self):

        command = "search host --host_environment prod --buildstatus ready" \
                  " --osname linux --osversion 6.1-x86_64 --archetype aquilon"
        out = self.commandtest(command.split())
        self.matchoutput(out, "aquilon91.aqd-unittest.ms.com",
                         command)

    def test_100_require_just(self):
        self.justificationmissingtest(["update_os", "--archetype", "aquilon", "--osname", "linux",
                                       "--osversion", "6.1-x86_64", "--lifecycle", "production"], auth=True,
                                      msgcheck=False)

    def test_110_not_require_just(self):
        self.noouttest(["update_os", "--archetype", "aquilon", "--osname", "linux",
                        "--osversion", "6.1-x86_64", "--comments", "'Comments are not "
                                                                   "harmful to change'"])

    def test_120_require_just_success(self):
        self.noouttest(["update_os", "--archetype", "aquilon", "--osname", "linux",
                        "--osversion", "6.1-x86_64", "--lifecycle", "production",
                        "--justification", "tcm=123"])
