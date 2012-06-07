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
""" Parameter data validation """
from datetime import datetime
from sqlalchemy import (Column, Integer, DateTime, Sequence, String,
                        Boolean, ForeignKey)
from sqlalchemy.orm import (relation, backref, deferred)
from aquilon.aqdb.model import Base, Archetype, Feature
from aquilon.aqdb.column_types import Enum
from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.column_types import AqStr
from sqlalchemy.types import Text

_TN = 'param_definition'
_PARAM_DEF_HOLDER = 'param_def_holder'
_PATH_TYPES = [ 'list', 'string', 'int', 'float', 'boolean', 'json' ]
_PARAM_DEF_HLDR_TYPES = [ 'archetype', 'feature' ]

class ParamDefinition(Base):
    """
        define parameter paths
    """

    __tablename__ = _TN
    __table_args__ = {'oracle_compress': True}

    id = Column(Integer, Sequence('%s_seq' % _TN), primary_key=True)
    path = Column(String(255), nullable=False)
    template = Column(String(32))
    required =  Column(Boolean(name="%s_paramdef_ck" % _TN),
                          default=False, nullable=False)
    value_type = Column(Enum(16, _PATH_TYPES), nullable=False, default="string")
    default = Column(Text, nullable=True)
    description = deferred(Column(String(255), nullable=True))
    holder_id = Column(Integer, ForeignKey('%s.id' % _PARAM_DEF_HOLDER,
                                           name='%s_holder_fk' % _TN,
                                           ondelete='CASCADE'))
    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    @property
    def template_base(self, base_object):
        return "%s/%s" % (base_object.name, self.template)

    @classmethod
    def validate_type(cls, value_type):
        """ Utility function for validating the value type """
        if value_type in _PATH_TYPES:
            return
        valid_types = ", ".join(sorted(_PATH_TYPES))
        raise ArgumentError("Unknown value type '%s'.  The valid types are: "
                            "%s." % (value_type, valid_types))

param_definition = ParamDefinition.__table__  # pylint: disable=C0103, E1101
param_definition.primary_key.name = '%s_pk' % _TN
param_definition.info['unique_fields'] = ['path', 'holder']

class ParamDefHolder (Base):
    """
    The dbobj with which this parameter paths are  associated with.
    """
    __tablename__ = _PARAM_DEF_HOLDER

    id = Column(Integer, Sequence('%s_seq' % _PARAM_DEF_HOLDER), primary_key=True)


    type = Column(AqStr(16), nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    __mapper_args__ = {'polymorphic_on': type}

    @property
    def holder_name(self):
        return None

    @property
    def holder_object(self):
        return None


param_definition_holder = ParamDefHolder.__table__  # pylint: disable=C0103, E1101
param_definition_holder.primary_key.name = '%s_pk' % _PARAM_DEF_HOLDER
param_definition_holder.info['unique_fields'] = ['id']
ParamDefinition.holder = relation(ParamDefHolder, uselist=False, lazy='subquery',
                            primaryjoin=ParamDefinition.holder_id==ParamDefHolder.id,
                            backref=backref('param_definitions',
                                            cascade='all, delete-orphan'))

class ArchetypeParamDef(ParamDefHolder):
    """ valid parameter paths which can be associated with this archetype """

    __mapper_args__ = {'polymorphic_identity': 'archetype'}

    archetype_id = Column(Integer,
                            ForeignKey('archetype.id',
                                       name='%s_archetype_fk' % _PARAM_DEF_HOLDER,
                                       ondelete='CASCADE'),
                            nullable=True)

    archetype = relation(Archetype, uselist=False, lazy='subquery',
                    backref=backref('paramdef_holder',
                                    cascade='all, delete-orphan',
                                    uselist=False))
    @property
    def holder_name(self):
        return "%s" % self.archetype.name  # pylint: disable=C0103, E1101

    @property
    def holder_object(self):
        return self.archetype

#Archetype.param_definitions = relation(ParamDefinition, secondary=param_definition_holder,
#                                  primaryjoin=Archetype.id==ArchetypeParamDef.archetype_id,
#                                  secondaryjoin=ParamDefHolder.id==ParamDefinition.holder_id,
#                                  viewonly=True)

class FeatureParamDef(ParamDefHolder):
    """ valid parameter paths which can be associated with this feature """

    __mapper_args__ = {'polymorphic_identity': 'feature'}

    feature_id = Column(Integer,
                            ForeignKey('feature.id',
                                       name='%s_feature_fk' % _PARAM_DEF_HOLDER,
                                       ondelete='CASCADE'),
                            nullable=True)

    feature = relation(Feature, uselist=False,
                    backref=backref('paramdef_holder',
                                    cascade='all, delete-orphan',
                                    uselist=False))
    @property
    def holder_name(self):
        return "%s" % self.feature.name  # pylint: disable=C0103, E1101

    @property
    def holder_object(self):
        return self.feature

#Feature.param_definitions = relation(ParamDefinition, secondary=param_definition_holder,
#                                  primaryjoin=Feature.id==FeatureParamDef.feature_id,
#                                  secondaryjoin=ParamDefHolder.id==ParamDefinition.holder_id,
#                                  viewonly=True)
