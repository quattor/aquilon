#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010  Contributor
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
dns = [ TestBrokerStart,
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


if __name__=='__main__':
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
