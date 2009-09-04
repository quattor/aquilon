#!/usr/bin/env python2.5
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009  Contributor
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
from utils import load_classpath, add, commit

load_classpath()

from aquilon.aqdb.db_factory import DbFactory
from aquilon.aqdb.model import EsxCluster, Archetype, Personality, Domain

from sqlalchemy import and_
from sqlalchemy.orm import join
from sqlalchemy.exc import IntegrityError

from nose.tools import raises

db = DbFactory()
sess = db.Session()

CLUSTER_NAME = 'test_esx_cluster'

def clean_up():
    del_cluster()

def del_cluster():
    cl = sess.query(EsxCluster).filter_by(name=CLUSTER_NAME).first()
    if cl:
        sess.delete(cl)
        commit(sess)
        print 'deleted test cluster'

def setup():
    print 'set up'
    clean_up()

def teardown():
    print 'tear down'
    clean_up()

def create_cluster():
    per = sess.query(Personality).select_from(
            join(Archetype, Personality)).filter(
            and_(Archetype.name=='windows', Personality.name=='generic')).one()
    domain = sess.query(Domain).filter_by(name='ny-prod').first()

    ec = EsxCluster(name=CLUSTER_NAME, personality=per, domain=domain)
    add(sess,ec)
    commit(sess)

    assert ec


def test_get_unique_against_polymorphic():
    create_cluster()
    ec = EsxCluster.get_unique(sess, CLUSTER_NAME)
    assert ec



if __name__ == "__main__":
    import nose
    nose.runmodule()
