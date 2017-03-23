#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013,2014,2015,2016  Contributor
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
"""Module for testing the generated profiles."""

import os
import gzip
import unittest

from lxml import etree

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestProfile(TestBrokerCommand):

    def load_profile(self, name):
        path = os.path.join(self.config.get("broker", "profilesdir"),
                            name + self.xml_suffix)
        self.assertTrue(os.path.exists(path))
        if self.gzip_profiles:
            path = gzip.open(path)
        tree = etree.parse(path)
        return tree

    def testunittest00sysloc(self):
        tree = self.load_profile("unittest00.one-nyp.ms.com")
        sysloc = tree.xpath("nlist[@name='hardware']/nlist[@name='sysloc']")
        self.assertEqual(len(sysloc), 1, "Number of sysloc elements was %d "
                         "instead of 1" % len(sysloc))
        sysloc = sysloc[0]

        campus = sysloc.xpath("string[@name='campus']")
        self.assertTrue(campus, "No campus in sysloc")
        campus = campus[0]
        self.assertEqual(campus.text, "ny", "Campus value was '%s' instead of ny"
                         % campus.text)

    def testaquilon61sysloc(self):
        tree = self.load_profile("aquilon61.aqd-unittest.ms.com")
        sysloc = tree.xpath("nlist[@name='hardware']/nlist[@name='sysloc']")
        self.assertEqual(len(sysloc), 1, "Number of sysloc elements was %d "
                         "instead of 1" % len(sysloc))

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestProfile)
    unittest.TextTestRunner(verbosity=2).run(suite)
