#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013,2015,2016,2017  Contributor
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
"""Module for testing the search building command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestSearchBuilding(TestBrokerCommand):
    def test_100_noinput(self):
        command = ["search", "building"]
        err = self.badoptiontest(command)
        self.matchoutput(err, "error: Please provide any of the required options!", command)

    def test_100_urivalid(self):
        command = ["search", "building", "--uri", "assetinventory://003428"]
        out = self.commandtest(command)
        self.output_equals(out, "bu", command)

    def test_100_uriinvalid(self):
        command = ["search", "building", "--uri", "invalid://123456"]
        self.noouttest(command)

    def test_100_proto(self):
        command = ["search", "building", "--uri", "assetinventory://003428", "--format", "proto"]
        model = self.protobuftest(command, expect=1)[0]
        self.assertEqual(model.name, "bu")
        self.assertEqual(model.uri, "assetinventory://003428")

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSearchBuilding)
    unittest.TextTestRunner(verbosity=2).run(suite)
