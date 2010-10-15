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
""" Test the host class """
from utils import load_classpath, commit, create, func_name, add
load_classpath()

from aquilon.aqdb.db_factory import DbFactory
from aquilon.aqdb.model import (Host, FutureARecord, Domain, Machine, Archetype,
                                Building, Personality, OperatingSystem, Status,
                                Model, Cpu, Vendor, DnsDomain, Network,
                                DnsEnvironment, Branch, PrimaryNameAssociation)

#from aquilon.aqdb.shell import ipshell

#FIXME: import server.depends from utils.load_server_classpath()
import ms.version
ms.version.addpkg('ipaddr', '2.0.0')
from ipaddr import IPv4Address as IPAddr

from nose.tools import eq_

NUM_MACHINES = 2
DNAME = 'ms.com'
DNSENV = 'internal'
SHORT_NAME_PREFIX = 'aqdb-test-host-'
MACHINE_NAME_PREFIX = 'test_machine_'

sess = DbFactory().Session()
assert sess, 'No session in %s' % func_name()

#TODO: factor out assert_type(obj, cls, func_name) the isinstance calls
STATUS = Status.get_unique(sess, 'ready')
assert isinstance(STATUS, Status), 'No ready status @ %s' % func_name()

DOMAIN = Domain.get_unique(sess, 'ny-prod')
assert isinstance(DOMAIN, Domain), 'no ny-prod domain @ %s' % func_name()

ARCH = Archetype.get_unique(sess, 'aquilon')
assert isinstance(ARCH, Archetype), 'No archetype @ %s' % func_name()

OS = OperatingSystem.get_unique(sess, name='linux', version='5.0-x86_64',
                                archetype=ARCH)
assert isinstance(OS, OperatingSystem), 'No os @ %s' % func_name()

PRSNLTY = Personality.get_unique(sess, name='generic', archetype=ARCH)
assert isinstance(PRSNLTY, Personality), 'no personality @ %s' % func_name()

NETWORK = sess.query(Network).filter(Network.cidr < 31).first()
assert isinstance(NETWORK, Network), 'no network in %s' % func_name()

DNS_DOMAIN = DnsDomain.get_unique(sess, DNAME)
assert isinstance(DNS_DOMAIN, DnsDomain), 'no dns domain @ %s' % func_name()

BRANCH = sess.query(Branch).first()
if not BRANCH:
    BRANCH = Branch(branch_type='domain', name='ny-prod', is_sync_valid=1,
                    compiler='/ms/dist/elfms/PROJ/panc/prod/lib/panc.jar',
                    autosync=1, owner_id=1)
    add(sess, BRANCH)
    commit(sess)
    print BRANCH


def teardown():
    #print '%s.teardown()' % func_name()

    a_records = sess.query(FutureARecord).filter(
        FutureARecord.name.like(SHORT_NAME_PREFIX+'%')).all()

    for rec in a_records:
        # this means that deleting the PNA deletes the host table.
        # is that how we want it? Yes, we don't know what it is without it.
        pna = sess.query(PrimaryNameAssociation).filter_by(a_record=rec).first()
        if pna:
            print 'deleting PrimaryNameAssoc for %s' % pna.hardware_entity
            sess.delete(pna)
            commit(sess)
        print 'deleting ARecord %s' % rec.fqdn
        sess.delete(rec)
        commit(sess)
    print 'deleted %s a_records' % len(a_records)

    machines = sess.query(Machine).filter(
        Machine.label.like(MACHINE_NAME_PREFIX+'%')).all()

    for machine in machines:
        if machine.host:
            sess.delete(machine.host)
        sess.delete(machine)
    commit(sess)
    print 'deleted %s machines' % len(machines)


def test_create_machines_for_test_host():
    np = Building.get_unique(sess, 'np')
    assert isinstance(np,Building), 'no building in %s' % func_name()

    hp = Vendor.get_unique(sess, 'hp')
    assert isinstance(hp, Vendor), 'no vendor in %s' % func_name()

    am = Model.get_unique(sess, name='bl45p', vendor=hp)
    assert isinstance(am, Model), 'no model in %s' % func_name()

    cpu = sess.query(Cpu).first()
    assert isinstance(cpu, Cpu), 'no cpu in %s' % func_name()

    for i in xrange(NUM_MACHINES):
        machine = Machine(label='%s%s'% (MACHINE_NAME_PREFIX, i), location=np,
                          model=am, cpu=cpu, cpu_quantity=2, memory=32768)
        create(sess, machine)

    machines = sess.query(Machine).filter(
        Machine.label.like(MACHINE_NAME_PREFIX+'%')).all()

    eq_(len(machines), NUM_MACHINES)


def machine_factory():
    """ Used to get a stream of newly minted machines to create hosts"""
    machines = sess.query(Machine).filter(
        Machine.label.like(MACHINE_NAME_PREFIX+'%')).all()
    size = len(machines)
    for machine in machines:
        yield machine

MACHINE_FACTORY = machine_factory()

#Just using the standard __init__ for now. Don't know if we'll want to
#do anything fancier than that just yet


def test_create_host_simple():
    for i in xrange(NUM_MACHINES):
        machine = MACHINE_FACTORY.next()
        #create an a_record for the primary name
        name = '%s%s' % (SHORT_NAME_PREFIX, i)

        #convert ip to ipaddr to int, add 1 (router) + i,
        #convert back to ip, then back to string
        #convoluted indeed (FIXME?)
        ip = str(IPAddr(int(IPAddr(NETWORK.ip)) + i +1 ))
        a_rec = FutureARecord.get_or_create(session=sess,
                                      fqdn='%s.ms.com' % name,
                                      ip=ip)

        BRANCH = sess.query(Branch).first()

        # make sure to delete them after (Or put in commit block?)
        sess.refresh(machine)
        host = Host(machine=machine, #primary_name_id=a_rec.id,
                    personality=PRSNLTY, status=STATUS, operating_system=OS,
                    branch=BRANCH)

        add(sess, host)

        pna = PrimaryNameAssociation(a_record_id=a_rec.id,
                                     hardware_entity_id=machine.machine_id)

        add(sess, pna)
        commit(sess)

    hosts = sess.query(Host).all()
    eq_(len(hosts), NUM_MACHINES)
    print 'created %s hosts'% len(hosts)

if __name__ == "__main__":
    import nose
    import nose_plugin
    nose.runmodule(exit=False, addplugins=[nose_plugin.DontRebuildPlugin()])
