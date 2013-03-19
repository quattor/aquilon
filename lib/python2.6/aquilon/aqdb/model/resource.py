# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
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

from sqlalchemy import (Column, Integer, String, DateTime, ForeignKey,
                        Sequence, UniqueConstraint)
from sqlalchemy.orm import relation, backref, validates

from aquilon.exceptions_ import InternalError
from aquilon.aqdb.column_types import AqStr
from aquilon.aqdb.model import Base, Cluster, Host

_TN = 'resource'
_ABV = 'res'
_RESHOLDER = 'resholder'


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
    def holder_name(self):  # pragma: no cover
        raise InternalError("Abstract base method called")

    @property
    def holder_object(self):  # pragma: no cover
        raise InternalError("Abstract base method called")

    @validates('resources')
    def _validate_resources(self, key, value):
        return self.validate_resources(key, value)

    def validate_resources(self, key, value):
        return value

    @property
    def holder_path(self):
        return "%s/%s" % (self.holder_type, self.holder_name)

resholder = ResourceHolder.__table__  # pylint: disable=C0103
resholder.primary_key.name = '%s_pk' % _RESHOLDER


class HostResource(ResourceHolder):
    __mapper_args__ = {'polymorphic_identity': 'host'}

    host_id = Column(Integer, ForeignKey('host.machine_id',
                                         name='%s_host_fk' % _RESHOLDER,
                                         ondelete='CASCADE'),
                     nullable=True)

    # This is a one-to-one relation, so we need uselist=False on the backref
    host = relation(Host,
                    backref=backref('resholder', uselist=False,
                                    cascade='all, delete-orphan'))

    @property
    def holder_name(self):
        return self.host.fqdn

    @property
    def holder_object(self):
        return self.host


resholder.append_constraint(UniqueConstraint('host_id',
                                             name='%s_host_uk' % _RESHOLDER))


class ClusterResource(ResourceHolder):
    __mapper_args__ = {'polymorphic_identity': 'cluster'}

    cluster_id = Column(Integer, ForeignKey('clstr.id',
                                            name='%s_clstr_fk' % _RESHOLDER,
                                            ondelete='CASCADE'),
                        nullable=True)

    # This is a one-to-one relation, so we need uselist=False on the backref
    cluster = relation(Cluster,
                       backref=backref('resholder', uselist=False,
                                       cascade='all, delete-orphan'))

    @property
    def holder_name(self):
        return self.cluster.name

    @property
    def holder_object(self):
        return self.cluster


resholder.append_constraint(UniqueConstraint('cluster_id',
                                             name='%s_cluster_uk' % _RESHOLDER))


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
                                           ondelete='CASCADE'),
                       nullable=False)

    holder = relation(ResourceHolder, innerjoin=True,
                      backref=backref('resources',
                                      cascade='all, delete-orphan'))

    # Uniqueness over just the resource name and holder_id - you can't
    # have filesystem 'foo' and intervention 'foo' attached to the same
    # host.  Done for sanity.
    UniqueConstraint('name', 'holder_id', name='%s_uk' % _TN)

    __mapper_args__ = {'polymorphic_on': resource_type}

    @property
    def template_base(self):
        return "resource/%s/%s/%s" % (self.holder.holder_path,
                                      self.resource_type,
                                      self.name)

    @validates('holder')
    def _validate_holder(self, key, value):
        return self.validate_holder(key, value)

    def validate_holder(self, key, value):
        return value

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
        return "<{0:c} Resource {0.name} of {1}>".format(self, self.holder)


resource = Resource.__table__  # pylint: disable=C0103
resource.primary_key.name = '%s_pk' % _TN
resource.info['unique_fields'] = ['name', 'holder']
