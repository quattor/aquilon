#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013  Contributor
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
"""Module for testing the rebind client command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestRebindClient(TestBrokerCommand):

    def testrebindafs(self):
        command = ["rebind", "client",
                   "--hostname", "unittest02.one-nyp.ms.com",
                   "--service", "afs", "--instance", "q.ln.ms.com"]
        (out, err) = self.successtest(command)
        self.matchoutput(err,
                         "unittest02.one-nyp.ms.com adding binding for "
                         "service afs instance q.ln.ms.com",
                         command)
        self.matchoutput(err,
                         "unittest02.one-nyp.ms.com removing binding for "
                         "service afs instance q.ny.ms.com",
                         command)

    def testverifyrebindafs(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Template: service/afs/q.ln.ms.com", command)

    def testverifyqny(self):
        command = ["cat", "--service", "afs", "--instance", "q.ny.ms.com",
                   "--server"]
        out = self.commandtest(command)
        self.matchclean(out, "unittest02.one-nyp.ms.com", command)

    def testverifyqln(self):
        command = ["cat", "--service", "afs", "--instance", "q.ln.ms.com",
                   "--server"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"clients" = list\(\s*"unittest02.one-nyp.ms.com"\s*\);',
                          command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRebindClient)
    unittest.TextTestRunner(verbosity=2).run(suite)
