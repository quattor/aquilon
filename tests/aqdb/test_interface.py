#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
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
""" Test interfaces and address_assignments """
import random
import logging
log = logging.getLogger('nose.aqdb.test_interface')

from utils import load_classpath, commit, create, func_name
load_classpath()

from aquilon.aqdb.db_factory import DbFactory
from aquilon.aqdb.model import Interface, Building, Cpu, Machine, Model, Vendor

from nose.tools import eq_, raises

NUM_MACHINES = 2
DNAME = 'ms.com'
DNSENV = 'internal'
SHORT_NAME_PREFIX = 'aqdb-test-host-'
MACHINE_NAME_PREFIX = 'test_machine_'

db = DbFactory()
sess = db.Session()


def random_mac():
    """ create random mac addresses for testing """
    mac = [0x00, random.randint(0x00, 0xff), random.randint(0x00, 0xff),
           random.randint(0x00, 0xff), random.randint(0x00, 0xff),
           random.randint(0x00, 0xff)]

    #TODO: use string formatting
    return ':'.join(map(lambda x: "%02x" % x, mac))


def teardown():
    machines = sess.query(Machine).filter(
        Machine.label.like(MACHINE_NAME_PREFIX + '%')).all()

    for machine in machines:
        if machine.interfaces:
            for iface in machine.interfaces:
                sess.delete(iface)
        sess.delete(machine)
    commit(sess)
    log.debug('deleted %s machines' % len(machines))


def test_create_machines_for_test_interface():
    np = Building.get_unique(sess, 'np')
    assert isinstance(np, Building), 'no building in %s' % func_name()

    hp = Vendor.get_unique(sess, 'hp')
    assert isinstance(hp, Vendor), 'no vendor in %s' % func_name()

    am = Model.get_unique(sess, name='bl45p', vendor=hp)
    assert isinstance(am, Model), 'no model in %s' % func_name()

    cpu = sess.query(Cpu).first()
    assert isinstance(cpu, Cpu), 'no cpu in %s' % func_name()

    for i in xrange(NUM_MACHINES):
        machine = Machine(label='%s%s' % (MACHINE_NAME_PREFIX, i), location=np,
                          model=am, cpu=cpu, cpu_quantity=2, memory=32768)
        create(sess, machine)

    machines = sess.query(Machine).filter(
        Machine.label.like(MACHINE_NAME_PREFIX + '%')).all()

    eq_(len(machines), NUM_MACHINES)


#create a bootable iface with no mac (fails)
@raises(ValueError)
def test_fail_bootable_iface_with_no_mac_addr():
    machine = sess.query(Machine).first()
    iface = Interface(machine=machine, name='eth3', interface_type='public',
                      bootable=True)


@raises(ValueError)
def test_fail_management_iface_with_no_mac_addr():
    machine = sess.query(Machine).first()
    iface = Interface(machine=machine, name='eth2',
                      interface_type='management')


@raises(ValueError)
def test_fail_upd_bootable_iface_to_null_mac():
    machine = sess.query(Machine).first()

    iface = Interface(hardware_entity=machine, name='eth1', mac=random_mac(),
                      bootable=True, interface_type='public')
    create(sess, iface)
    assert isinstance(iface, Interface), 'no iface created @ %s' % func_name()

    iface.mac = None
    commit(sess)

    assert iface.mac is not None, 'able to set a bootable interface to null'


@raises(ValueError)
def test_fail_upd_mgmt_iface_to_null_mac():
    machine = sess.query(Machine).first()

    iface = Interface(hardware_entity=machine, name='ipmi', mac=random_mac(),
                      bootable=True, interface_type='management')
    create(sess, iface)
    assert isinstance(iface, Interface), 'no iface created @ %s' % func_name()

    iface.mac = None
    commit(sess)

    assert iface.mac is not None, 'set a management iface to null mac_addr'


def test_create_iface():
    machine = sess.query(Machine).first()

    iface = Interface(hardware_entity=machine, name='eth0', mac=random_mac(),
                      bootable=True, interface_type='public')
    create(sess, iface)
    assert isinstance(iface, Interface), 'no iface created @ %s' % func_name()


def test_iface_str():
    """ excersize aqdb.interface.__str__ """
    machine = sess.query(Machine).first()
    log.info(machine.interfaces)

    #looks odd, but exercises the backref while we're at it
    print '%s has %s' % (machine.interfaces[0].hardware_entity,
                         machine.interfaces[0])


if __name__ == "__main__":
    import nose
    nose.runmodule()
