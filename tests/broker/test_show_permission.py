#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2018  Contributor
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
"""Module for testing the show permission command."""

import unittest
import getpass

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestShowPermission(TestBrokerCommand):
    def test_100_role_nobody(self):
        command = ["show_permission", "--role", "nobody"]
        out = self.commandtest(command)
        self.matchoutput(out, "show_share", command)
        self.matchoutput(out, "dump_dns", command)
        self.matchoutput(out, "cat", command)
        self.matchoutput(out, "status", command)

    def test_105_role_aqd_admin(self):
        command = ["show_permission", "--role", "aqd_admin"]
        out = self.commandtest(command)
        self.matchoutput(out, "add_user", command)
        self.matchoutput(out, "grant_root_access", command)
        self.matchoutput(out, "add_host", command)
        self.matchoutput(out, "show_os", command)

    def test_107_role_unittester(self):
        command = ["show_permission", "--role", "unittester"]
        out = self.commandtest(command)
        self.matchoutput(out, "update_review", command)
        self.matchoutput(out, "add_rack (expect with: --bunker, --room)",
                         command)
        self.matchoutput(out, "del_interface (only with: --network_device, "
                         "--switch)", command)

    def test_110_unexisting_role(self):
        command = ["show_permission", "--role", "tototo"]
        err = self.badrequesttest(command)
        self.matchoutput(err, "Bad Request: tototo role doesn't exist\n",
                         command)

    def test_200_command_add_grn(self):
        command = ["show_permission", "--command", "add_grn"]
        out = self.commandtest(command)
        self.matchoutput(out, "aqd_admin", command)
        self.matchoutput(out, "engineering", command)

    def test_205_unexisting_command(self):
        command = ["show_permission", "--command", "bonjour"]
        err = self.badrequesttest(command)
        self.matchoutput(err, "Bad Request: bonjour command does not exist\n",
                         command)

    def test_210_command_update_service(self):
        command = ["show_permission", "--command", "update_service"]
        out = self.commandtest(command)
        self.matchoutput(out, "operations", command)
        self.matchoutput(out, "engineering", command)
        self.matchoutput(out, "unittester", command)

    def test_215_command_update_service_option_instance(self):
        command = ["show_permission", "--command", "update_service",
                   "--option", "instance"]
        out = self.commandtest(command)
        self.matchoutput(out, "aqd_admin", command)
        self.matchoutput(out, "unittester", command)
        self.matchclean(out, "engineering", command)

    def test_217_command_update_service_bad_option(self):
        command = ["show_permission", "--command", "update_service",
                   "--option", "bad"]
        err = self.badrequesttest(command)
        self.matchoutput(err, "bad option does not exist in "
                         "update_service command", command)

    def test_220_command_update_service_no_option(self):
        command = ["show_permission", "--command", "update_service",
                   "--no-option"]
        out = self.commandtest(command)
        self.matchoutput(out, "aqd_admin", command)
        self.matchoutput(out, "engineering", command)
        self.matchclean(out, "unittester", command)

    def test_300_username_cdb(self):
        command = ["show_permission", "--username", "cdb"]
        out = self.commandtest(command)
        self.matchoutput(out, "add_user", command)
        self.matchoutput(out, "show_cpu", command)

    def test_305_unexisting_username(self):
        command = ["show_permission", "--username", "testusername"]
        err = self.badrequesttest(command)
        self.matchoutput(err, "User testusername not found", command)

    def test_310_username_no_realm(self):
        command = ["show_permission", "--username", getpass.getuser()]
        err = self.badrequesttest(command)
        self.matchoutput(err,
                         "More than one user found for this name:",
                         command)

    def test_315_username_realm(self):
        command = ["show_permission", "--username", getpass.getuser(),
                   "--realm", self.realm]
        out = self.commandtest(command)
        self.matchoutput(out, "show_city", command)

    def test_320_no_option(self):
        command = ["show_permission"]
        out = self.commandtest(command)
        self.matchoutput(out, "show_alias", command)

    def test_400_bad_arguments(self):
        command = ["show_permission", "--command", "add_user", "--role",
                   "aqd_admin"]
        err = self.badoptiontest(command)
        self.matchoutput(err, "provide exactly one of the required options!",
                         command)
