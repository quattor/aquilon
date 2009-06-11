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
""" tables/classes applying to clusters """
from datetime import datetime

from sqlalchemy import (Column, Integer, String, DateTime, Sequence, ForeignKey,
                        UniqueConstraint)

from sqlalchemy.orm import relation, backref
from sqlalchemy.ext.associationproxy import association_proxy

from aquilon.aqdb.column_types.aqstr import AqStr
from aquilon.aqdb.model import (Base, Host, Service, Location, Personality,
                                ServiceInstance, Machine)


#cluster is a reserved word in oracle
_TN = 'clstr'
class Cluster(Base):
    """
        A group of two or more hosts for high availablility or grid capabilities
    """
    __tablename__ = _TN

    id = Column(Integer, Sequence('%s_seq'%(_TN)), primary_key=True)
    cluster_type = Column(AqStr(16), nullable=False)
    name = Column(AqStr(64), nullable=False)

    #Lack of cascaded deletion is intentional on personality
    personality_id = Column(Integer, ForeignKey('personality.id',
                                                name='%s_prsnlty_fk'),
                            nullable=False)

    location_constraint_id = Column(ForeignKey('location.id',
                                               name='clstr_loc_fk'))

    max_members = Column(Integer, default=2, nullable=True) #TODO: have EsxCluster override default
    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments      = Column(String(255))

    location_constraint = relation(Location,
                                   uselist=False,
                                   lazy=False)

    #TODO: backref?
    personality = relation(Personality, uselist=False, lazy=False)

    members = association_proxy('cluster', 'host')
    #TODO: an append that checks the max_members

    __mapper_args__ = {'polymorphic_on': cluster_type}

cluster = Cluster.__table__
cluster.primary_key.name = '%s_pk'% (_TN)
cluster.append_constraint(UniqueConstraint('name', 'cluster_type', name='%s_uk'%(_TN)))

table = cluster #FIXME: remove the need for these

def _esx_cluster_vm_by_vm(vm):
    """ creator function for esx cluster vms"""
    return EsxClusterVM(vm=vm)

class EsxCluster(Cluster):
    """
        Specifically for our VMware esx based clusters.
    """
    __tablename__ = 'esx_cluster'
    __mapper_args__ = {'polymorphic_identity': 'esx'}

    esx_cluster_id = Column(Integer, ForeignKey('%s.id'%(_TN),
                                            name='esx_cluster_fk',
                                            ondelete='CASCADE'),
                            #if the cluster record is deleted so is esx_cluster
                            primary_key=True)

    vm_to_host_ratio = Column(Integer, default=16, nullable=True)

    vms = association_proxy('esx_cluster', 'vm', creator=_esx_cluster_vm_by_vm)

    #TODO: proxy my metacluster as an attribute if I have one?

    def __init__(self, **kw):
        kw['max_members'] = 8
        super(EsxCluster, self).__init__(**kw)

esx_cluster = EsxCluster.__table__
esx_cluster.primary_key.name = 'esx_%s_pk'


_ECM = 'esx_cluster_member'
class EsxClusterMember(Base):
    """ Specific Class for EsxCluster vmhosts """
    __tablename__ = _ECM

    esx_cluster_id = Column(Integer, ForeignKey('esx_cluster.esx_cluster_id',
                                                name='esx_cluster_cluster_fk',
                                                ondelete='CASCADE'),
                            primary_key=True)

    #VMHOSTS only. TODO: validate host archetype?
    host_id = Column(Integer, ForeignKey('host.id',
                                         name='%s_host_fk'%(_ECM),
                                         ondelete='CASCADE'),
                        primary_key=True)

    creation_date = Column(DateTime, default=datetime.now, nullable=False)

    cluster = relation(EsxCluster, uselist=False, lazy=False,
                       backref=backref('cluster', cascade='all, delete-orphan'))

    host = relation(Host, lazy=False, cascade='all',
                    backref=backref('host', cascade='all, delete-orphan'))

    def __init__(self, **kw):
        cl = kw['cluster']
        host = kw['host']

        if len(cl.members) == cl.max_members:
            msg = '%s already at maximum capacity (%s)'% (cl.name,
                                                          cl.max_members)
            raise ValueError(msg)

        if host.archetype.name != 'vmhost':
            msg = "host %s must be archetype 'vmhost' (is %s)"% (host.fqdn,
                                                                host.archetype.name)
            raise ValueError(msg)
        #TODO: enforce cluster members are inside the location constraint?
        super(EsxClusterMember, self).__init__(**kw)

ecm = EsxClusterMember.__table__
ecm.primary_key.name = '%s_pk'% (_ECM)

_ECVM = 'esx_cluster_vm'
class EsxClusterVM(Base):
    """ Binds virtual machines to EsxClusters """
    __tablename__ = _ECVM

    esx_cluster_id = Column(Integer, ForeignKey('esx_cluster.esx_cluster_id',
                                                name='%s_cluster_fk'%(_ECVM),
                                                ondelete='CASCADE'),
                            primary_key=True)

    machine_id = Column(Integer, ForeignKey('machine.machine_id',
                                            name='%s_machine_fk'%(_ECVM),
                                            ondelete='CASCADE'),
                        primary_key=True)

    creation_date = Column(DateTime, default=datetime.now, nullable=False)

    esx_cluster = relation(EsxCluster, uselist=False, lazy=False,
                       backref=backref('esx_cluster', cascade='all, delete-orphan'))

    vm = relation(Machine, lazy=False, cascade='all',
                  backref=backref('vm', cascade='all, delete-orphan'))

ecvm = EsxClusterVM.__table__
ecvm.primary_key.name = '%s_pk'% (_ECVM)
ecvm.append_constraint(UniqueConstraint('machine_id', name='%s_uk'%(_ECVM)))

_CRS = 'cluster_aligned_service'
_ABV = 'clstr_alnd_svc'
class ClusterAlignedService(Base):
    """
        Express services that must be the same for cluster types. As SQL Alchemy
        doesn't yet support FK or functionally determined discrimators for
        polymorphic inheritance, cluster_type is currently being expressed as a
        string. As ESX is the only type for now, it's seems a reasonable corner
        to cut.
    """
    __tablename__ = _CRS

    service_id = Column(Integer, ForeignKey('service.id',
                                            name='%s_svc_fk'%(_ABV),
                                            ondelete='CASCADE'),
                        nullable=False)

    cluster_type = Column(AqStr(16), primary_key=True)

    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments = Column(String(255))

    service = relation(Service, cascade='all', uselist=False)

cas = ClusterAlignedService.__table__
cas.primary_key.name = '%s_pk'%(_ABV)

_CS = 'cluster_service'
_CAB = 'clstr_svc'
class ClusterService(Base):
    """
        Makes bindings of service instances to clusters
    """
    __tablename__ = _CS
    cluster_id = Column(Integer, ForeignKey('%s.id'%(_TN),
                                            name='%s_cluster_fk'%(_CAB),
                                            ondelete='CASCADE'),
                        primary_key=True)

    #cfg_path will die soon. using service instance here to ease later transition
    service_instance_id = Column(Integer, ForeignKey('service_instance.id',
                                                     name='%s_srv_inst_fk'%(_CAB)),
                                 primary_key=True)

    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments = Column(String(255))

    #can't set the backref name to one that's already in use
    cluster = relation(Cluster, uselist=False, lazy=False,
                       backref=backref('thecluster', cascade='all, delete-orphan'))

    service_instance = relation(ServiceInstance, lazy=False, backref='service_instance')

    @property
    def cfg_path(self):
        return self.service_instance.cfg_path

#should it check if its a required service?
