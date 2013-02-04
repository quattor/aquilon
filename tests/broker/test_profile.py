#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2013  Contributor
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
"""Module for testing the generated profiles."""


import os
import unittest
from lxml import etree
import gzip

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestProfile(TestBrokerCommand):

    def load_profile(self, name):
        path = os.path.join(self.config.get("broker", "profilesdir"),
                            name + self.profile_suffix)
        self.failUnless(os.path.exists(path))
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
        self.failUnless(campus, "No campus in sysloc")
        campus = campus[0]
        self.assertEqual(campus.text, "ny", "Campus value was '%s' instead of ny"
                         % campus.text)

        domains = sysloc.xpath("list[@name='dns_search_domains']/string")
        self.failUnless(domains, "No DNS search domains set")
        searchlist = [e.text for e in domains]
        # DNS maps:
        # - aqd-unittest.ms.com comes from rack ut3
        # - utroom1 also has aqd-unittest.ms.com mapped _after_ td1 and td2,
        #   but the rack mapping is more specific, so aqd-unittest.ms.com
        #   remains at the beginning
        # - new-york.ms.com comes from the campus
        expect = ['aqd-unittest.ms.com', 'td1.aqd-unittest.ms.com',
                  'td2.aqd-unittest.ms.com', 'new-york.ms.com']
        self.assertEqual(searchlist, expect,
                         "dns_search_domains in sysloc was %s instead of %s" %
                         (repr(searchlist), repr(expect)))

    def testaquilon61sysloc(self):
        tree = self.load_profile("aquilon61.aqd-unittest.ms.com")
        sysloc = tree.xpath("nlist[@name='hardware']/nlist[@name='sysloc']")
        self.assertEqual(len(sysloc), 1, "Number of sysloc elements was %d "
                         "instead of 1" % len(sysloc))
        sysloc = sysloc[0]

        domains = sysloc.xpath("list[@name='dns_search_domains']/string")
        self.failUnless(domains, "No DNS search domains set")
        searchlist = [e.text for e in domains]
        # Not in utroom1, so no (td[12].)?aqd-unittest.ms.com
        expect = ['new-york.ms.com']
        self.assertEqual(searchlist, expect,
                         "dns_search_domains in sysloc was %s instead of %s" %
                         (repr(searchlist), repr(expect)))

    def testresolver(self):
        tree = self.load_profile("unittest00.one-nyp.ms.com")
        rs = tree.xpath("nlist[@name='software']/nlist[@name='components']/nlist[@name='resolver']")
        self.assertEqual(len(rs), 1, "Number of resolver elements was %d "
                         "instead of 1" % len(rs))
        rs = rs[0]

        searchlist = [e.text for e in rs.xpath("list[@name='search']/string")]
        # DNS maps:
        # - aqd-unittest.ms.com comes from rack ut3
        # - utroom1 also has aqd-unittest.ms.com mapped _after_ td1 and td2,
        #   but the rack mapping is more specific, so aqd-unittest.ms.com
        #   remains at the beginning
        # - new-york.ms.com comes from the campus
        # - ms.com comes from DEFAULT_DOMAIN in aquilon/archetype/base.tpl
        expect = ['aqd-unittest.ms.com', 'td1.aqd-unittest.ms.com',
                  'td2.aqd-unittest.ms.com', 'new-york.ms.com', 'ms.com']
        self.assertEqual(searchlist, expect,
                         "search list in resolver was %s instead of %s" %
                         (repr(searchlist), repr(expect)))

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestProfile)
    unittest.TextTestRunner(verbosity=2).run(suite)
