#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2013  Contributor
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
"""Module for testing the show campus command.

Most of the location show commands are tested in their add/del
counterparts.  However, we have chosen (so far) to not implement
those commands for campus.

"""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestShowCampus(TestBrokerCommand):

    def testshowcampusall(self):
        command = "show campus --all"
        out = self.commandtest(command.split(" "))
        # Just a sampling.
        self.matchoutput(out, "Campus: ny", command)
        self.matchoutput(out, "Fullname: New York", command)
        self.matchoutput(out, "Campus: vi", command)
        self.matchoutput(out, "Fullname: Virginia", command)

    def testshowcampusvi(self):
        command = "show campus --campus vi"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Campus: vi", command)
        self.matchoutput(out, "Fullname: Virginia", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestShowCampus)
    unittest.TextTestRunner(verbosity=2).run(suite)
