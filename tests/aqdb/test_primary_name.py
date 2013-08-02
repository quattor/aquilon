#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2012,2013  Contributor
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
""" Perform the tests for DNS Records """
import logging
import itertools

from utils import load_classpath, add, commit, create, func_name
load_classpath()

from test_machine import add_machine, del_machines
from test_dns import get_reqs

from nose.tools import raises, eq_
from sqlalchemy.exc import IntegrityError

from aquilon.aqdb.db_factory import DbFactory
from aquilon.aqdb.model import (DnsRecord, ARecord, DnsDomain, DnsEnvironment,
                                PrimaryNameAssociation, Machine)

logging.basicConfig()
log = logging.getLogger('nose.aqdb')

db = DbFactory()
sess = db.Session()

DNS_DOMAIN_NAME = 'ms.com'
DNS_ENV = 'internal'
AREC_PREFIX = 'primary-name-record-'
IP_ADDRS = ['172.17.148.128', '172.17.148.129', '172.17.148.130']

MCHN_PREFIX = 'primary_name_test_machine_'
unique_number = itertools.count(0)

dns_count_b4 = machine_count_by = pna_count_b4 = None
pna_count_b4 = sess.query(PrimaryNameAssociation).count()
dns_count_b4 = sess.query(DnsRecord).count()
mchn_count_b4 = sess.query(Machine).count()

log.info('counts:\nARecords: %s Machines: %s PNAs: %s' % (
    dns_count_b4, mchn_count_b4, pna_count_b4))

def teardown():
    sess.close()
    (ms, intrnl) = get_reqs()

    #TODO: move this general approach to test_dns???
    # generalize the entire approach and take a count on the way in and out
    qry = sess.query(ARecord).filter(
        ARecord.name.like(AREC_PREFIX + '%'))
    qry = qry.filter_by(dns_environment=intrnl)
    if qry.count() == 0:
        log.info('successful cascaded deletion of ARecords')
    else:
        log.error('ARecords left intact when they should be delete cascaded')
    for rec in qry.filter_by(dns_domain=ms).all():
        sess.delete(rec)
        commit(sess)
        log.debug('deleted ARecord %s' % rec.fqdn)

    dns_count_after = sess.query(DnsRecord).count()

    if dns_count_after != dns_count_b4:
        log.warning('%s record(s) left after teardown in %s, should be %s' % (
            dns_count_after, func_name(), dns_count_b4))

    del_machines(sess, MCHN_PREFIX)

    mchn_count_after = sess.query(Machine).count()
    if mchn_count_b4 != mchn_count_after:
        log.warning('%s machines left after %s, should be %s'%(
            mchn_count_after, func_name(), mchn_count_b4))

def setup():
    dmn = DnsDomain.get_unique(sess, DNS_DOMAIN_NAME, compel=True)
    assert isinstance(dmn, DnsDomain), 'No ms.com domain in %s' % func_name()

    intrnl = DnsEnvironment.get_unique(sess, DNS_ENV, compel=True)
    assert isinstance(dmn, DnsDomain), 'No internal env in %s' % func_name()


#TODO: move to test_dns???
def add_arecord(ip):
    """ adding a valid ARecord """
    (ms, intrnl) = get_reqs()
    a_rcrd = ARecord(name=AREC_PREFIX + str(unique_number.next()),
                     dns_domain=ms, dns_environment=intrnl,
                     ip=ip, comments='comment here', session=sess)
    create(sess, a_rcrd)

    assert a_rcrd, 'no a_record created by %s' % func_name()
    sess.refresh(a_rcrd)

    return a_rcrd


def test_primary_name():
    mchn = add_machine(sess, MCHN_PREFIX + str(unique_number.next()))
    #log.debug('created machine %s' % str(mchn.__dict__))

    (ms, intrnl) = get_reqs()
    a_rcrd = add_arecord(IP_ADDRS[0])
    #log.debug(a_rcrd.__dict__)

    pna = PrimaryNameAssociation(a_record_id=a_rcrd.dns_record_id,
                                 hardware_entity=mchn)

    create(sess, pna)
    log.info(pna)


@raises(IntegrityError)
def test_no_duplicate_primary_name_entries():
    """ Ensures that a primary name can not be duplicated """

    a_rcrd = sess.query(ARecord).filter_by(ip=IP_ADDRS[0]).first()
    assert a_rcrd, 'No a_record in %s' % func_name()

    mchn = add_machine(sess, MCHN_PREFIX + str(unique_number.next()))
    assert mchn, 'no machine created in %s' % func_name()

    try:
        pna = PrimaryNameAssociation(hardware_entity=mchn, a_record=a_rcrd)
                                     #a_record_id=a_rcrd.dns_record_id)
        sess.add(pna)
        sess.commit()
        print 'should fail but %r ' % pna
    except Exception, e:
        sess.rollback()
        raise e
    #finally:
        #sess.close()
        #sess.rollback()


def test_primary_name_cascaded_deletion():
    """ Ensure desired cascade behavior happens """

    #sess.expunge_all()
    #db.engine.echo = True
    logging.getLogger('sqlalchemy.orm').setLevel(logging.DEBUG)

    pna_count_b4 = sess.query(PrimaryNameAssociation).count()
    log.info('count before pna delete is %s' % pna_count_b4)


    mchn = sess.query(Machine).filter(
    Machine.label.like(MCHN_PREFIX + '%')).first()
    assert mchn, 'no machine found in %s' % func_name()

    #logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


    try:
        sess.delete(mchn)
        sess.commit()
    except Exception, e:
        sess.close()
        raise e

    logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
    logging.getLogger('sqlalchemy.orm').setLevel(logging.ERROR)

    #db.engine.echo = False
    #commit(sess)
    #sess.expunge_all()

    pna_count_after = sess.query(PrimaryNameAssociation).count()
    log.info('pna count after machine delete is %s' % pna_count_after)
    eq_(pna_count_after, pna_count_b4 - 1)

#TODO: ensure this cascades all the way to the ARecord.

#TODO: test that the operation is restricted or fails when you try to delete
#      the dns record.

#def test_primary_name_fails_shouldnt():
#    mchn = add_machine(sess, MCHN_PREFIX+'2', 'bl45p')
#    print 'created %s' % mchn
#
#    (ms, intrnl) = get_reqs()
#    a_rcrd = sess.query(ARecord).filter_by(ip=IP_ADDR).first()
#
#    # WHY DOES THIS BAIL!?!?!?!
#    try:
#        pna = PrimaryNameAssociation(a_record=a_rcrd, hardware_entity=mchn)
#    except Exception, e:
#        sess.rollback()
#        sess.close()
#        print e


if __name__ == "__main__":
    import nose
    nose.runmodule()
