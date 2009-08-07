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
from aquilon.aqdb.model import (Building, Personality, Archetype, Cluster,
                                EsxCluster, MetaCluster, MetaClusterMember)

from sqlalchemy import and_
from sqlalchemy.orm import join
from sqlalchemy.exc import IntegrityError

from nose.tools import raises

db = DbFactory()
sess = db.Session()

CLUSTER_NAME = 'test_esx_cluster'
META_NAME = 'test_meta_cluster'
NUM_CLUSTERS = 30
M2 = 'test_meta_cluster2'
M3 = 'test_meta_cluster3'

def clean_up():
    del_metas()
    del_clusters()

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
        print '%s clusters before deleting metas'%(sess.query(Cluster).count())
        for m in mlist:
            sess.delete(m)
        commit(sess)
        print 'deleted %s metaclusters'%(len(mlist))
        print '%s clusters left after deleting metas'%(sess.query(Cluster).count())

def setup():
    print 'set up'
    clean_up()

def teardown():
    print 'tear down'
    clean_up()


def test_create_clusters():
    np = sess.query(Building).filter_by(name='np').one()
    per = sess.query(Personality).select_from(
            join(Archetype, Personality)).filter(
            and_(Archetype.name=='windows', Personality.name=='generic')).one()

    for i in xrange(NUM_CLUSTERS):
        ec = EsxCluster(name='%s%s'%(CLUSTER_NAME,i),
                        location_constraint=np,
                        personality=per)
        add(sess, ec)
    commit(sess)

    ecs = sess.query(EsxCluster).all()
    assert len(ecs) is NUM_CLUSTERS
    print ecs[0]

    assert ecs[0].max_hosts is 8
    print 'esx cluster max hosts = %s'%(ecs[0].max_hosts)


def cluster_factory():
    clusters = sess.query(EsxCluster).all()
    size = len(clusters)
    for cl in clusters:
        yield cl

cl_factory = cluster_factory()

def test_create_metacluster():
    mc = MetaCluster(name=META_NAME)
    add(sess, mc)
    commit(sess)

    assert mc
    print mc


def test_add_meta_member():
    """ Test adding a cluster to a metacluster and cluster.metacluster """
    mc = MetaCluster.get_by('name', META_NAME, sess)[0]
    cl = cl_factory.next()

    mcm = MetaClusterMember(metacluster=mc, cluster=cl)
    add(sess, mcm)
    commit(sess)

    assert mcm
    assert len(mc.members) is 1
    print 'metacluster members %s'%(mc.members)

    assert cl.metacluster is mc
    print cl.metacluster

@raises(ValueError)
def test_add_too_many_metacluster_members():
    cl2 = cl_factory.next()
    cl3 = cl_factory.next()
    assert cl2
    assert cl3

    mc = MetaCluster.get_unique(sess, META_NAME)
    mcm2 = MetaClusterMember(metacluster=mc, cluster=cl2)
    add(sess, mcm2)
    commit(sess)
    assert mcm2

    mcm3 = MetaClusterMember(metacluster=mc, cluster=cl3)
    add(sess, mcm3)
    commit(sess)
    assert mcm3

@raises(IntegrityError, AssertionError)
def test_two_metaclusters():
    """ Test unique constraint against cluster """
    m2 = MetaCluster(name=M2)
    m3 = MetaCluster(name=M3)
    sess.add_all([m2, m3])
    commit(sess)
    assert m2
    assert m3

    cl4 = cl_factory.next()
    assert cl4

    mcm1=MetaClusterMember(metacluster=m2, cluster=cl4)
    add(sess, mcm1)
    commit(sess)
    assert mcm1

    mcm2=MetaClusterMember(metacluster=m3, cluster=cl4)
    add(sess, mcm1)
    commit(sess)
    assert mcm2


def test_append():
    mc=MetaCluster.get_unique(sess, M3)
    assert len(mc.members) is 0
    print '%s before append test has members %s'%(mc, mc.members)

    cl5 = cl_factory.next()
    assert cl5
    print cl5

    mc.members.append(cl5)
    commit(sess)
    assert len(mc.members) is 1
    print 'members now %s'%(mc.members)

if __name__ == "__main__":
    import nose
    nose.runmodule()
