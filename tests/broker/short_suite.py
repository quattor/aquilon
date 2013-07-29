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
""" A leaner set of broker suite definitions.

    Now imports the full suite directly from orderedsuite. Synchronization
    to the main suite is no longer required.
"""

import utils
utils.load_classpath()
import nose

from test_start import TestBrokerStart
from test_stop import TestBrokerStop
from test_ping import TestPing
from test_add_building import TestAddBuilding
from test_add_network import TestAddNetwork
from test_del_network import TestDelNetwork
from test_del_building import TestDelBuilding

from test_add_dns_domain import TestAddDnsDomain
from test_del_dns_domain import TestDelDnsDomain
from test_add_dns_records import TestAddDnsRecords
from test_del_dns_records import TestDelDnsRecords
from test_map_dns_domain import TestMapDnsDomain
from test_unmap_dns_domain import TestUnmapDnsDomain

#TODO: have TestBrokerStart/Stop as fixtures, not tests
dns = [TestBrokerStart,
       ### ADDS ###
       TestPing, TestAddDnsDomain, TestAddBuilding, TestMapDnsDomain,
       TestAddNetwork, TestAddDnsRecords,
       ### DELETES ###
       TestDelDnsRecords, TestUnmapDnsDomain, TestDelNetwork,
       TestDelDnsDomain, TestDelBuilding,
       ### TEAR DOWN ###
       TestBrokerStop]

tiny = [TestBrokerStart, TestPing, TestBrokerStop]

suites = {'tiny': tiny, 'dns': dns}


class MySuite(nose.suite.ContextSuite):
    def __init__(self, tests='tiny', *args, **kwargs):

        nose.suite.ContextSuite.__init__(self, *args, **kwargs)
        loader = nose.loader.TestLoader()
        for t in suites[tests]:
            self.addTest(loader.loadTestsFromTestCase(t))


if __name__ == '__main__':
    import sys
    import orderedsuite

    suite = None

    if 'full' in sys.argv:
        suite = orderedsuite.BrokerTestSuite()
    else:
        for k in suites.keys():
            if k in sys.argv:
                suite = MySuite(tests=k)

    if not suite:
        suite = MySuite()

    nose.run(suite=suite)
