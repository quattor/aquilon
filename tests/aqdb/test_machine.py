#!/usr/bin/env python2.5
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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
import unittest
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
    delete_machines(sess, NAME)

def setup():
    print 'setup'
    cleanup()

def teardown():
    print 'teardown'
    cleanup()


def create_machine(sess, name, model):
    """ Shorthand to create machines created for the purposes of reuse
        among all the various tests that require them """

    model = Model.get_by('name', model, sess)[0]
    assert model, "Can't find model %s"%(model)

    proc = sess.query(Cpu).first()
    assert proc, "Can't find a cpu"

    rack = sess.query(Rack).first()
    assert rack, "Can't find a rack"

    mchn = Machine(name=name, model=model, location=rack, cpu=proc)
    add(sess, mchn)
    commit(sess)

    return mchn

def delete_machines(sess=sess, prefix=NAME):
    """ deletes all machines with names like prefix% """

    machines = sess.query(Machine).filter(Machine.name.like(prefix+'%')).all()
    if machines:
        for machine in machines:
            sess.delete(machine)
        commit(sess)
        print 'deleted %s machines'%(len(machines))

def test_create_machine():
    """ test creating a machine """
    mchn = create_machine(sess, NAME, MODEL)
    assert mchn, 'Commit machine failed'
    print mchn

def test_del_machine():
    mchn = sess.query(Machine).filter_by(name = NAME).first()
    if mchn:
        sess.delete(mchn)
        commit(sess)

        t = sess.query(Machine).filter_by(name = NAME).first()
        assert t is None
        print 'deleted machine'
