#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010  Contributor
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
from utils import load_classpath, commit, create, func_name

load_classpath()

from aquilon.aqdb.db_factory import DbFactory
from aquilon.aqdb.model import (Archetype, Building, Cluster, Personality,
                                Service, ServiceInstance, EsxCluster, Domain,
                                ClusterAlignedService, ClusterServiceBinding)

from sqlalchemy import and_
from sqlalchemy.orm import join
from sqlalchemy.exc import InvalidRequestError

from nose.tools import raises

db = DbFactory()
sess = db.Session()

CLUSTER_NAME = 'test_esx_cluster'
SVC_NAME = 'test_esx_management'
INST_NAME = 'test_esx_manager'
DOMAIN = 'ny-prod'

#for testing cascaded deletion
SVC_2 = 'test_svc_delete_me'

def setup():
    clean_up()

def teardown():
    clean_up()


def clean_up():
    del_cluster_service()
    del_cluster_aligned_svc()
    del_service_instance(INST_NAME)
    del_service(SVC_NAME)
    del_clusters()


def del_clusters():
    clist = sess.query(Cluster).all()
    if len(clist) > 0:
        for c in clist:
            sess.delete(c)
        commit(sess)
        print 'deleted %s cluster(s)' % len(clist)

def del_cluster_member():
    ech = sess.query(EsxClusterMember).filter(Host.name==HOST_NAME).first()
    if ech:
        sess.delete(ech)
        commit(sess)
        print 'deleted cluster host'

def del_service_instance(name):
    si = sess.query(ServiceInstance).filter_by(name=name).first()
    if si:
        count = sess.query(ServiceInstance).filter_by(name=name).delete()
        commit(sess)
        print 'called del_service_instance(%s), deleted %s rows'% (name, count)

def del_service(name):
    ''' reusable service delete for other tests '''
    svc = sess.query(Service).filter_by(name=name).first()
    if svc:
        count = sess.query(Service).filter_by(name=name).delete()
        commit(sess)
        print 'session.delete(%s) deleted %s rows'% (name, count)


def del_cluster_service():
    sess.query(ClusterServiceBinding).delete()
    commit(sess)
    print 'deleted cluster service binding'

def del_cluster_aligned_svc():
    sess.query(ClusterAlignedService).delete()
    commit(sess)
    print 'deleted cluster aligned service'


def add_service(sess, name):
    ''' reusable add service code for other tests '''
    svc = sess.query(Service).filter_by(name=name).first()
    if not svc:
        svc=Service(name=name)
        create(sess, svc)
    return svc

def test_add_service():
    svc = sess.query(Service).filter_by(name=SVC_NAME).first()
    if not svc:
        svc = add_service(sess, SVC_NAME)
        assert svc, 'service not created by %s' % func_name()
        print svc

def test_create_cluster():
    #TODO: make this a reusable function in test_cluster and import
    np = sess.query(Building).filter_by(name='np').one()
    dmn = sess.query(Domain).first()
    assert dmn, 'No domain found in %s' % func_name()
    per = sess.query(Personality).select_from(
            join(Archetype, Personality)).filter(
            and_(Archetype.name=='windows', Personality.name=='generic')).one()

    ec = EsxCluster(name=CLUSTER_NAME, location_constraint=np, personality=per,
            domain=dmn)

    create(sess, ec)

    assert ec, "No EsxCluster created by %s" % func_name()
    print ec

def test_add_aligned_service():
    svc = sess.query(Service).filter_by(name=SVC_NAME).first()
    assert svc, 'No cluster management service in %s'% func_name()

    cas = ClusterAlignedService(cluster_type='esx', service=svc)
    create(sess, cas)
    assert cas, 'no cluster aligned service created by %s' % func_name()
    print cas

    ec = sess.query(EsxCluster).first()
    print '%s has required services %s'% (ec.name, ec.required_services)
    assert ec.required_services


def add_service_instance(sess, service_name, name):
    si = sess.query(ServiceInstance).filter_by(name=name).first()
    if not si:
        print 'Creating %s instance %s ' % (service_name, name)

        svc = sess.query(Service).filter_by(name=service_name).one()
        assert svc, 'No %s service in %s' % (service_name, func_name())

        si = ServiceInstance(name=name, service=svc)
        create(sess, si)
        assert si, 'no service instance created by %s' % func_name()
    return si

def test_cluster_bound_svc():
    """ test the creation of a cluster bound service """
    si = add_service_instance(sess, SVC_NAME, INST_NAME)
    assert si, 'no service instance in %s'% func_name()

    ec = Cluster.get_unique(sess, CLUSTER_NAME)
    cs = ClusterServiceBinding(cluster=ec, service_instance=si)
    create(sess, cs)

    assert cs, 'no cluster bound service created by' % func_name()
    print cs

def test_cluster_service_binding_assoc_proxy():
    """ tests the association proxy on cluster to service works """
    ec = Cluster.get_unique(sess, CLUSTER_NAME)
    assert ec
    print 'length of %s.service_bindings is %s' % (ec.name,
                                                   len(ec.service_bindings))
    assert len(ec.service_bindings) is 1

def test_cascaded_delete_1():
    """ test that deleting service bindings don't delete services """

    print 'Creating throw away service'
    svc = add_service(sess, SVC_2)

    assert svc, 'service not created by %s' % func_name()
    print 'added throw away service %s' % (svc)

    #make it a cluster aligned svc
    cas = ClusterAlignedService(cluster_type='esx', service=svc)
    create(sess, cas)
    assert cas, "No cluster aligned service in %s" % func_name()

    """
        delete the cas, see if the service is still there. sess.refresh(obj)
        will throw 'InvalidRequestError: Instance xxx is not persistent within
        this Session' if it's been deleted
    """
    sess.delete(cas)
    commit(sess)
    sess.refresh(svc)
    assert svc, "Service deleted when deleting the cluster aligned service"
    print "still have %s after deleting cluster aligned svc" % svc

@raises(InvalidRequestError)
def test_cascaded_delete2():
    """ deleting services deletes cluster aligned services """
    svc = sess.query(Service).filter_by(name=SVC_2).first()
    assert svc, "No throw away service in %s" % func_name()

    #add cas, delete the service, make sure the CAS disappears
    cas = ClusterAlignedService(cluster_type='esx', service=svc)
    create(sess, cas)
    assert cas, "No cluster aligned service in %s" % func_name()

    #FIX ME: put in tear_down()
    sess.delete(svc)
    commit(sess)
    sess.refresh(cas)
    sess.refresh(svc)


if __name__ == "__main__":
    import nose
    nose.runmodule()
