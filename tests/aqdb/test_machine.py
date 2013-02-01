#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2013  Contributor
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
