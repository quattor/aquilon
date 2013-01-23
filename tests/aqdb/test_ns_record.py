#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011  Contributor
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

