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
