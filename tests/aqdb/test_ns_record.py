#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013  Contributor
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
""" Perform testing on NS Records """

from utils import load_classpath, commit, create, func_name
load_classpath()

from ipaddr import IPv4Address, IPv4Network

from aquilon.aqdb.db_factory import DbFactory
from aquilon.aqdb.model import DnsDomain, NsRecord, Network, Building
from aquilon.aqdb.model import FutureARecord as ARecord

db = DbFactory()
sess = db.Session()

DNS_DOMAIN_NAME = 'aqdbtest.ms.com'
AREC_NAME = 'test-a-record'
TEST_NET = '1.1.1.0/24'
TEST_NET_NAME = 'aqdb_test_net'
TEST_IP = '1.1.1.2'


def setup():
    dmn = DnsDomain(name=DNS_DOMAIN_NAME)
    create(sess, dmn)
    assert dmn, 'no dns domain in %s' % func_name()

    pi = Building.get_unique(sess, name='pi', compel=True)

    n = IPv4Network(TEST_NET)
    net = Network(name=TEST_NET_NAME, network=n, location=pi)
    create(sess, net)
    assert net, 'no network created by %s' % func_name()

    ip = IPv4Address(TEST_IP)
    arec = ARecord(name=AREC_NAME, dns_domain=dmn, ip=ip, network=net)
    create(sess, arec)
    assert arec, 'no ARecord created by %s' % func_name()

def teardown():
    ip = IPv4Address(TEST_IP)
    arec = ARecord.get_unique(sess, fqdn='%s.%s' % (AREC_NAME, DNS_DOMAIN_NAME),
                              compel=True)
    dmn = DnsDomain.get_unique(sess, DNS_DOMAIN_NAME, compel=True)

    #Test deletion of NSRecord doesn't affect the ARecord or DNS Domain
    #by deleting it first.
    ns = NsRecord.get_unique(sess, a_record=arec, dns_domain=dmn)
    sess.delete(ns)
    commit(sess)

    sess.delete(arec)
    commit(sess)

    sess.delete(dmn)
    commit(sess)

    sess.query(Network).filter_by(name=TEST_NET_NAME).delete()
    commit(sess)


def test_ns_record():
    """ test creating a valid ns record """

    tgt = ARecord.get_unique(sess,
                             fqdn='%s.%s' % (AREC_NAME, DNS_DOMAIN_NAME),
                             compel=True)

    dmn = DnsDomain.get_unique(sess, name=DNS_DOMAIN_NAME, compel=True)

    ns = NsRecord(a_record=tgt, dns_domain=dmn)
    create(sess, ns)
    assert ns, 'No NS Record created in test_ns_record'
    print 'created %s' % ns

    assert dmn.servers, 'No name server association proxy in test_ns_record'

