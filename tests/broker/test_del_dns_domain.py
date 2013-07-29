#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Module for testing the del dns_domain command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelDnsDomain(TestBrokerCommand):
    """ test delete dns functionality """

    def testdelaqdunittestdomain(self):
        self.dsdb_expect("delete_dns_domain -domain_name aqd-unittest.ms.com")
        command = "del dns_domain --dns_domain aqd-unittest.ms.com"
        self.noouttest(command.split(" "))
        self.dsdb_verify()

    def testverifydelaqdunittestdomain(self):
        command = "show dns_domain --dns_domain aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testverifydelaqdunittestdomainproto(self):
        command = ["show", "dns_domain", "--dns_domain=aqd-unittest.ms.com",
                   "--format=proto"]
        self.notfoundtest(command)

    def testverifyshowall(self):
        command = "show dns_domain --all"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "DNS Domain: aqd-unittest.ms.com", command)

    def testverifyfqdns(self):
        command = ["search", "dns", "--dns_domain", "aqd-unittest.ms.com"]
        self.notfoundtest(command)

    def testverifyshowallproto(self):
        command = "show dns_domain --all --format=proto"
        out = self.commandtest(command.split(" "))
        dns_domains = self.parse_dns_domainlist_msg(out).dns_domains
        dns_names = [d.name for d in dns_domains]
        for domain in ['aqd-unittest.ms.com']:
            self.failIf(domain in dns_names,
                        "Domain %s appears in list %s" % (domain, dns_names))

    def testdeltd1(self):
        self.dsdb_expect("delete_dns_domain -domain_name td1.aqd-unittest.ms.com")
        command = ["del", "dns", "domain",
                   "--dns_domain", "td1.aqd-unittest.ms.com"]
        self.noouttest(command)
        self.dsdb_verify()

    def testdeltd2(self):
        self.dsdb_expect("delete_dns_domain -domain_name td2.aqd-unittest.ms.com")
        command = ["del", "dns", "domain",
                   "--dns_domain", "td2.aqd-unittest.ms.com"]
        self.noouttest(command)
        self.dsdb_verify()

    def testdeltd3(self):
        """ test delete domain with dsdb failure """

        test_domain = "td3.aqd-unittest.ms.com"
        self.dsdb_expect("add_dns_domain -domain_name %s -comments " % test_domain)
        command = ["add", "dns", "domain", "--dns_domain", test_domain]
        self.noouttest(command)
        self.dsdb_verify()

        errstr = "DNS domain %s doesn't exists" % test_domain
        self.dsdb_expect("delete_dns_domain -domain_name %s" % test_domain, True, errstr)
        command = ["del", "dns", "domain", "--dns_domain", test_domain]
        out, err = self.successtest(command)
        self.matchoutput(err,
                         "The DNS domain td3.aqd-unittest.ms.com does not "
                         "exist in DSDB, proceeding.",
                         command)
        self.dsdb_verify()


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelDnsDomain)
    unittest.TextTestRunner(verbosity=2).run(suite)
