#!/usr/bin/env python2.6
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
"""Module for testing the update srv record command."""


import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUpdateSrvRecord(TestBrokerCommand):

    def test_100_update(self):
        command = ["update", "srv", "record", "--service", "kerberos",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "arecord14.aqd-unittest.ms.com",
                   "--weight", 15, "--priority", 25, "--port", "8888",
                   "--comments", "SRV comments"]
        self.noouttest(command)

    def test_200_verify(self):
        command = ["search", "dns", "--fullinfo", "--record_type", "srv",
                   "--target", "arecord14.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Weight: 15", command)
        self.matchoutput(out, "Priority: 25", command)
        self.matchoutput(out, "Port: 8888", command)
        self.matchoutput(out, "Comments: SRV comments", command)

    def test_300_missing(self):
        command = ["update", "srv", "record", "--service", "no-such-service",
                   "--protocol", "tcp", "--dns_domain", "aqd-unittest.ms.com",
                   "--target", "arecord14.aqd-unittest.ms.com",
                   "--weight", 15, "--priority", 25, "--port", "8888",
                   "--comments", "SRV comments"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "SRV Record _no-such-service._tcp.aqd-unittest.ms.com, "
                         "DNS environment internal not found.",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateSrvRecord)
    unittest.TextTestRunner(verbosity=2).run(suite)
