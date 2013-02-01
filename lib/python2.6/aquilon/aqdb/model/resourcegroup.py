# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012  Contributor
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

from sqlalchemy import Integer, Column, ForeignKey

from aquilon.aqdb.model import Resource, ResourceHolder
from aquilon.aqdb.column_types.aqstr import AqStr
from aquilon.exceptions_ import ArgumentError
from sqlalchemy.orm import relation, backref


_TN = 'resourcegroup'
_RESHOLDER = 'resholder'


class ResourceGroup(Resource):
    """ A collection of resources which operate together
        (e.g. a VCS Service Group)."""
    __tablename__ = _TN
    __mapper_args__ = {'polymorphic_identity': 'resourcegroup'}
    _class_label = 'Resource Group'

    id = Column(Integer, ForeignKey('resource.id',
                                    name='rg_resource_fk',
                                    ondelete='CASCADE'),
                                    primary_key=True)

    # declare any per-group attributes here (none for now)

    # This is to enforce the same type of resources in the group
    required_type = Column(AqStr(32), nullable=True)

    def validate_holder(self, key, value):
        if isinstance(value, BundleResource):
            raise ValueError("ResourceGroups must not be held by other " +
                             "ResourceGroups")
        return value

    @property
    def branch(self):
        return self.holder.holder_object.branch


resourcegroup = ResourceGroup.__table__
resourcegroup.primary_key.name = '%s_pk' % (_TN)
resourcegroup.info['unique_fields'] = ['holder', 'name']


class BundleResource(ResourceHolder):
    '''Allow ResourceGroups to hold other types of resource. '''
    # Note: the polymorphic identity of ResourceGroup and BundleResource should
    # be the same, because plenary paths sometimes use one or the other,
    # depending on the context. These two classes should really be one if there
    # was a sane way to support multiple inheritance in the DB, so their
    # identities should at least be the same.
    __mapper_args__ = {'polymorphic_identity': 'resourcegroup'}

    resourcegroup_id = Column(Integer, ForeignKey('resourcegroup.id',
                                           name='%s_bundle_fk' % _RESHOLDER,
                                           ondelete='CASCADE',
                                           use_alter=True),
                        nullable=True)

    # This is a one-to-one relation, so we need uselist=False on the backref
    resourcegroup = relation(ResourceGroup, lazy='subquery',
                             primaryjoin=resourcegroup_id == ResourceGroup.id,
                             backref=backref('resholder',
                                             cascade='all, delete-orphan',
                                             uselist=False))

    def validate_resources(self, key, value):
        rg = self.resourcegroup
        if rg.required_type and rg.required_type != value.resource_type:
            raise ArgumentError("Resource's %s type differs from the requested"
                                " %s" % (value.resource_type, rg.required_type))

        return value

    @property
    def holder_name(self):
        return self.resourcegroup.name

    @property
    def holder_object(self):
        return self.resourcegroup

    @property
    def holder_path(self):
        return "%s/%s/%s" % (self.resourcegroup.holder.holder_path,
                             self.holder_type,
                             self.holder_name)
