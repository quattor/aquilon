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
from aquilon.aqdb.model import (Vendor, Model, Machine, Cpu, Building, Domain,
                                DnsDomain, Status, Personality, Archetype, Host,
                                Cluster, EsxCluster, EsxClusterMember, Service,
                                ServiceInstance, Tld, CfgPath, ClusterService,
                                ClusterAlignedService, EsxClusterVM)

from sqlalchemy import and_
from sqlalchemy.orm import join
from sqlalchemy.exc import IntegrityError

#from nose.plugins.attrib import attr
from nose.tools import raises

db = DbFactory()
sess = db.Session()

MACHINE_NAME = 'test_esx_machine'
HOST_NAME = 'test_esx_host'
CLUSTER_NAME = 'test_esx_cluster'
C2 = 'test_cluster2'
C3 = 'test_cluster3'


def clean_up():
    del_host()
    del_cluster_member()
    del_machine()
    del_clusters()

def del_machine():
    mach = sess.query(Machine).filter_by(name=MACHINE_NAME).first()
    if mach:
        sess.delete(mach)
        commit(sess)
        print 'deleted machine'

def del_host():
    hst = sess.query(Host).filter_by(name=HOST_NAME).first()
    if hst:
        sess.delete(hst)
        commit(sess)
        print 'deleted host'

def del_clusters():
    clist = sess.query(Cluster).all()
    if len(clist) > 0:
        for c in clist:
            sess.delete(c)
        commit(sess)
        print 'deleted %s cluster(s)'%(len(clist))

def del_cluster_member():
    ech = sess.query(EsxClusterMember).filter(Host.name==HOST_NAME).first()
    if ech:
        sess.delete(ech)
        commit(sess)
        print 'deleted cluster host'

def setup():
    print 'set up'
    clean_up()

def teardown():
    print 'tear down'
    clean_up()

def test_create_machine():
    np = Building.get_by('name', 'np', sess)[0]
    am = Model.get_by('name', 'aurora_model', sess)[0]
    a_cpu = Cpu.get_by('name', 'aurora_cpu', sess)[0]

    vm_machine = Machine(name=MACHINE_NAME, location=np, model=am,
                         cpu=a_cpu, cpu_quantity=8, memory=32768)
    sess.add(vm_machine)
    commit(sess)

    print vm_machine
    assert(vm_machine)

def test_create_host():
    dmn = Domain.get_by('name', 'daqscott', sess)[0]
    dns_dmn = DnsDomain.get_by('name', 'one-nyp.ms.com', sess)[0]
    stat = Status.get_by('name', 'build', sess)[0]

    pers = sess.query(Personality).select_from(
        join(Personality, Archetype)).filter(
        and_(Archetype.name=='vmhost', Personality.name=='generic')).one()

    vm_machine = Machine.get_by('name', MACHINE_NAME, sess)[0]
    print vm_machine

    sess.autoflush=False
    vm_host = Host(machine=vm_machine, name=HOST_NAME, dns_domain=dns_dmn,
               domain=dmn, personality=pers, status=stat)
    sess.add(vm_host)
    sess.autoflush=True

    commit(sess)

    print vm_host
    assert(vm_host)

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

def test_add_cluster_host():
    vm_host = Host.get_by('name', HOST_NAME, sess)[0]
    ec = EsxCluster.get_by('name', CLUSTER_NAME, sess)[0]
    ech = EsxClusterMember(host=vm_host, cluster=ec)

    sess.add(ech)
    commit(sess)

    assert ech
    print ech

    assert ec.members
    assert len(ec.members) is 1
    print 'cluster members: %s'%(ec.members)



#TODO: def too_many_cluster_members():
#create 9 vmhosts

#TODO: esx cluster member table: test __init__ method for other invalid archetypes

#Gateway
