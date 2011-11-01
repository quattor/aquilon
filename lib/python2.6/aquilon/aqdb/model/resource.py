# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011  Contributor
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

from datetime import datetime
import re

from sqlalchemy import (Column, Integer, String, DateTime, ForeignKey,
                        Sequence, UniqueConstraint, CheckConstraint)
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relation, backref, object_session

from aquilon.aqdb.column_types import AqStr, Enum
from aquilon.aqdb.model import Base, Cluster, Host

_TN = 'resource'
_ABV = 'res'
_RESHOLDER = 'resholder'


class Resource(Base):
    """
        Abstraction of specific tables (e.g. VM or Filesystem) into a resource

        A resource is a generic bundle that can be attached to hosts or
        clusters. The resource can take on different shapes such as a VM
        or a filesystem, but there are many common operations we want
        to perform on them and therefore we map the specific types of
        bundles into this Resource class.
    """
    __tablename__ = _TN

    id = Column(Integer, Sequence('%s_seq' % _TN), primary_key=True)
    resource_type = Column(AqStr(16), nullable=False)
    name = Column(AqStr(64), nullable=False)
    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments = Column(String(255), nullable=True)
    holder_id = Column(Integer, ForeignKey('%s.id' % _RESHOLDER,
                                           name='%s_resholder_fk' % _TN,
                                           ondelete='CASCADE'))

    # Uniqueness over just the resource name and holder_id - you can't
    # have filesystem 'foo' and intervention 'foo' attached to the same
    # host.  Done for sanity.
    UniqueConstraint('name', 'holder_id', name='%s_uk' % _TN)

    __mapper_args__ = {'polymorphic_on': resource_type}

    @property
    def template_base(self):
        return "resource/%s/%s/%s/%s" % (self.resource_type,
                                         self.holder.holder_type,
                                         self.holder.holder_name,
                                         self.name)

    def __lt__(self, other):
        # Quick optimizations to not have to evaluate the name.
        if self.holder != other.holder:
            if self.holder.holder_type != other.holder.holder_type:
                return self.holder.holder_type < other.holder.holder_type
            return self.holder.holder_name < other.holder.holder_name
        if self.resource_type != other.resource_type:
            return self.resource_type < other.resource_type
        return self.name < other.name

    def __repr__(self):
        return "<%s Resource %s>" % (self.resource_type, self.id)


resource = Resource.__table__ # pylint: disable-msg=C0103, E1101
resource.primary_key.name = '%s_pk' % _TN
resource.info['unique_fields'] = ['name', 'holder']


class ResourceHolder(Base):
    """
    Who owns this resource? This could be a variety of different
    owners (e.g. a host, a cluster) and so we have a polymorphic class
    to represent this ownership - that enforces that only a single class
    can ever have ownership. We enforce uniqueness of (resource name,
    resourceholder). As an example, you could have a filesystem resource
    called 'root' on many hosts.
    """
    __tablename__ = _RESHOLDER

    id = Column(Integer, Sequence('%s_seq' % _RESHOLDER), primary_key=True)

    # I don't like this as a string...
    holder_type = Column(AqStr(16), nullable=False)
    __mapper_args__ = {'polymorphic_on': holder_type}

    @property
    def holder_name(self):
        return None

    @property
    def holder_object(self):
        return None


Resource.holder = relation(ResourceHolder, uselist=False, lazy='subquery',
                           primaryjoin=Resource.holder_id==ResourceHolder.id,
                           backref=backref('resources',
                                           cascade='all, delete-orphan'))

resholder = ResourceHolder.__table__  # pylint: disable-msg=C0103, E1101
resholder.primary_key.name = '%s_pk' % _RESHOLDER


class HostResource(ResourceHolder):
    __mapper_args__ = {'polymorphic_identity': 'host'}

    host_id = Column(Integer, ForeignKey('host.machine_id',
                                         name='%s_host_fk' % _RESHOLDER,
                                         ondelete='CASCADE'),
                     nullable=True)

    host = relation(Host, uselist=False, lazy='subquery',
                    backref=backref('resholder',
                                    cascade='all, delete-orphan',
                                    uselist=False))

    @property
    def holder_name(self):
        return self.host.fqdn

    @property
    def holder_object(self):
        return self.host


class ClusterResource(ResourceHolder):
    __mapper_args__ = {'polymorphic_identity': 'cluster'}

    cluster_id = Column(Integer, ForeignKey('clstr.id',
                                            name='%s_clstr_fk' % _RESHOLDER,
                                            ondelete='CASCADE'),
                        nullable=True)

    cluster = relation(Cluster, uselist=False, lazy='subquery',
                       backref=backref('resholder',
                                       cascade='all, delete-orphan',
                                       uselist=False))

    @property
    def holder_name(self):
        return self.cluster.name

    @property
    def holder_object(self):
        return self.cluster


Host.resources = relation(
    Resource, secondary=resholder,
    primaryjoin=Host.machine_id==HostResource.host_id,
    secondaryjoin=ResourceHolder.id==Resource.holder_id,
    viewonly=True)

Cluster.resources = relation(
    Resource, secondary=resholder,
    primaryjoin=Cluster.id==ClusterResource.cluster_id,
    secondaryjoin=ResourceHolder.id==Resource.holder_id,
    viewonly=True)
