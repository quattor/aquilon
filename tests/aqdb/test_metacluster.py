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
from utils import load_classpath, commit

load_classpath()

from aquilon.aqdb.db_factory import DbFactory
from aquilon.aqdb.model import (Building, Personality, Archetype, Cluster,
                                EsxCluster, EsxClusterMember, MetaCluster,
                                MetaClusterMember)

from sqlalchemy import and_
from sqlalchemy.orm import join
from sqlalchemy.exc import IntegrityError

from nose.tools import raises

db = DbFactory()
sess = db.Session()

CLUSTER_NAME = 'test_esx_cluster'
META_NAME = 'test_meta_cluster'
C2 = 'test_cluster2'
C3 = 'test_cluster3'
M2 = 'test_meta_cluster2'
M3 = 'test_meta_cluster3'

def clean_up():
    del_meta_members()
    del_metas()
    del_clusters()

#TODO: refactor into a single delete method
def del_clusters():
    clist = sess.query(Cluster).all()
    if len(clist) > 0:
        for c in clist:
            sess.delete(c)
        commit(sess)
        print 'deleted %s cluster(s)'%(len(clist))

def del_metas():
    mlist = sess.query(MetaCluster).all()
    if len(mlist) > 0:
        for m in mlist:
            sess.delete(m)
        commit(sess)
        print 'deleted metacluster'

def del_meta_members():
    mlist = sess.query(MetaClusterMember).all()
    if len(mlist) > 0:
        for m in mlist:
            sess.delete(m)
            commit(sess)
        print 'deleted %s metacluster members'%(len(mlist))

def setup():
    print 'set up'
    clean_up()

def teardown():
    print 'tear down'
    #clean_up()


def test_create_cluster():
    np = sess.query(Building).filter_by(name='np').one()
    per = sess.query(Personality).select_from(
            join(Archetype, Personality)).filter(
            and_(Archetype.name=='windows', Personality.name=='generic')).one()

    ec = EsxCluster(name=CLUSTER_NAME, location_constraint=np, personality=per)

    sess.add(ec)
    commit(sess)

    assert ec
    print ec

    assert ec.max_members is 8
    print 'esx cluster max members = %s'%(ec.max_members)

def test_add_meta():
    mc = MetaCluster(name=META_NAME)
    sess.add(mc)
    commit(sess)

    assert mc
    print mc


def test_add_meta_member():
    mc = MetaCluster.get_by('name', META_NAME, sess)[0]
    cl = Cluster.get_by('name', CLUSTER_NAME, sess)[0]

    mcm = MetaClusterMember(metacluster=mc, cluster=cl)
    sess.add(mcm)
    commit(sess)

    assert mcm
    assert len(mc.members) is 1
    print 'metacluster members %s'%(mc.members)

@raises(ValueError)
def test_add_too_many_metacluster_members():
    mc = MetaCluster.get_by('name', META_NAME, sess)[0]
    per = sess.query(Personality).select_from(
            join(Archetype, Personality)).filter(
            and_(Archetype.name=='windows', Personality.name=='generic')).one()
    cl2 = EsxCluster(name=C2, personality=per)
    cl3 = EsxCluster(name=C3, personality=per)

    mcm2 = MetaClusterMember(metacluster=mc, cluster=cl2)
    sess.add_all([cl2, cl3, mcm2])
    commit(sess)

    assert mcm2
    assert cl2
    assert cl3

    mcm3 = MetaClusterMember(metacluster=mc, cluster=cl3)
    sess.add(mcm3)
    commit(sess)
    assert mcm3

@raises(IntegrityError)
def test_two_metaclusters():
    """ Test unique constraint against cluster """
    m2 = MetaCluster(name=M2)
    m3 = MetaCluster(name=M3)
    sess.add_all([m2, m3])
    commit(sess)
    assert m2
    assert m3

    cl3 = EsxCluster.get_by('name', C3, sess)[0]
    assert cl3

    mcm1=MetaClusterMember(metacluster=m2, cluster=cl3)
    sess.add(mcm1)
    commit(sess)
    assert mcm1

    mcm2=MetaClusterMember(metacluster=m3, cluster=cl3)
    sess.add(mcm1)
    commit(sess)
    assert mcm2

if __name__ == "__main__":
    import nose
    nose.runmodule()
