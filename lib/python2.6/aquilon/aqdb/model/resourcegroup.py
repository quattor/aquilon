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

from sqlalchemy import (Integer, DateTime, Sequence, String, Column, Boolean,
                        UniqueConstraint, CheckConstraint, ForeignKey)

from aquilon.aqdb.model import Resource, ResourceHolder
from aquilon.aqdb.column_types.aqstr import AqStr
from sqlalchemy.orm import relation, backref, object_session


_TN = 'resourcegroup'
_RESHOLDER = 'resholder'


class ResourceGroup(Resource):
    """ A collection of resources which operate together
        (e.g. a VCS Service Group) """
    __tablename__ = _TN
    __mapper_args__ = {'polymorphic_identity': 'resourcegroup'}

    id = Column(Integer, ForeignKey('resource.id',
                                    name='rg_resource_fk',
                                    ondelete='CASCADE'),
                                    primary_key=True)

    # declare any per-group attributes here (none for now)


resourcegroup = ResourceGroup.__table__
resourcegroup.primary_key.name = '%s_pk' % (_TN)
# resources are namespaced by their holder, but holders are uniquely named.
# Since resourcegroups are both we have to decide which pattern to follow.
# We choose to make the names globally unique
resourcegroup.info['unique_fields'] = ['name']


class BundleResource(ResourceHolder):
    '''Allow ResourceGroups to hold other types of resource. '''
    __mapper_args__ = {'polymorphic_identity': 'bundle'}
    resourcegroup_id = Column(Integer, ForeignKey('resource.id',
                                           name='%s_bundle_fk' % _RESHOLDER,
                                           ondelete='CASCADE',
                                           use_alter=True),
                        nullable=True)

    resourcegroup = relation(ResourceGroup, uselist=False, lazy='subquery',
                             primaryjoin=resourcegroup_id==ResourceGroup.id,
                             backref=backref('resholder',
                                             cascade='all, delete-orphan',
                                             uselist=False))

    @property
    def holder_name(self):
        return self.resourcegroup.name

    @property
    def holder_object(self):
        return self.resourcegroup


resholder = ResourceHolder.__table__
ResourceGroup.resources = relation(
     Resource, secondary=resholder,
     primaryjoin=ResourceGroup.id==BundleResource.resourcegroup_id,
     secondaryjoin=ResourceHolder.id==Resource.holder_id,
     foreign_keys=[resholder.c.resourcegroup_id, resholder.c.id],
     viewonly=True, single_parent=True)
