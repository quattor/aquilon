#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2013  Contributor
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
""" tests create and delete of a machine through the session """
import logging
log = logging.getLogger('nose.aqdb.test_machine')

from utils import load_classpath, add, commit
load_classpath()

from sqlalchemy import and_
from sqlalchemy.orm import join

import aquilon.aqdb.depends
from aquilon.aqdb.db_factory import DbFactory
from aquilon.aqdb.model import Vendor, Model, Machine, Cpu, Rack

db = DbFactory()
sess = db.Session()
NAME = 'test_machine'
MODEL='bl45p'

def cleanup():
    del_machines(sess, NAME)
    pass

def setup():
    print 'setup'
    cleanup()

def teardown():
    print 'teardown'
    cleanup()


def add_machine(sess, name, model=MODEL):
    """ Shorthand to create machines created for the purposes of reuse
        among all the various tests that require them """
    mchn = sess.query(Machine).filter_by(label=name).first()
    if mchn:
        return mchn

    model = Model.get_unique(sess, name=model, compel=True)

    proc = sess.query(Cpu).first()
    assert proc, "Can't find a cpu"

    rack = sess.query(Rack).first()
    assert rack, "Can't find a rack"

    mchn = Machine(label=name, model=model, location=rack, cpu=proc)
    add(sess, mchn)
    commit(sess)

    return mchn


def del_machines(sess=sess, prefix=NAME):
    """ deletes all machines with names like prefix% """
    machines = sess.query(Machine).filter(
        Machine.label.like(prefix + '%')).all()

    if machines:
        log.debug('attempting to delete %s machines' % len(machines))
        for machine in machines:
            log.info('deleting %s' % machine)
            sess.delete(machine)
            commit(sess)


def test_add_machine():
    """ test creating a machine """
    mchn = add_machine(sess, NAME, MODEL)
    assert mchn, 'Commit machine failed'
    print mchn.name
    log.info(mchn)

def test_get_unique_by_label():
    """ test machine.get_unique """
    mchn = Machine.get_unique(sess, NAME, compel=True)
    assert mchn, 'get_unique failure for machine'
    print mchn

def test_del_machine():
    mchn = sess.query(Machine).filter_by(label=NAME).first()
    if mchn:
        sess.delete(mchn)
        commit(sess)

        t = sess.query(Machine).filter_by(label=NAME).first()
        assert t is None
        log.info('deleted machine')
