# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" Parameter data validation """

from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, Sequence, String,
                        Boolean, Text, ForeignKey, UniqueConstraint, Index)
from sqlalchemy.orm import (relation, backref, deferred)

from aquilon.aqdb.model import Base, Archetype, Feature
from aquilon.aqdb.column_types import Enum
from aquilon.exceptions_ import ArgumentError, InternalError
from aquilon.aqdb.column_types import AqStr

_TN = 'param_definition'
_PARAM_DEF_HOLDER = 'param_def_holder'
_PATH_TYPES = ['list', 'string', 'int', 'float', 'boolean', 'json']


class ParamDefHolder(Base):
    """
    The dbobj with which this parameter paths are  associated with.
    """
    __tablename__ = _PARAM_DEF_HOLDER
    _class_label = 'Parameter Definition Holder'
    _instance_label = 'holder_name'

    id = Column(Integer, Sequence('%s_seq' % _PARAM_DEF_HOLDER), primary_key=True)

    type = Column(AqStr(16), nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    __mapper_args__ = {'polymorphic_on': type}

    @property
    def holder_name(self):  # pragma: no cover
        raise InternalError("Abstract base method called")

    @property
    def holder_object(self):  # pragma: no cover
        raise InternalError("Abstract base method called")


param_definition_holder = ParamDefHolder.__table__  # pylint: disable=C0103
param_definition_holder.info['unique_fields'] = ['id']


class ArchetypeParamDef(ParamDefHolder):
    """ valid parameter paths which can be associated with this archetype """

    __mapper_args__ = {'polymorphic_identity': 'archetype'}

    archetype_id = Column(Integer,
                          ForeignKey('archetype.id',
                                     name='%s_archetype_fk' % _PARAM_DEF_HOLDER,
                                     ondelete='CASCADE'),
                          nullable=True)

    archetype = relation(Archetype,
                         backref=backref('paramdef_holder', uselist=False,
                                         cascade='all, delete-orphan'))

    __extra_table_args__ = (UniqueConstraint(archetype_id,
                                             name='param_def_holder_archetype_uk'),)

    @property
    def holder_name(self):
        return "%s" % self.archetype.name  # pylint: disable=C0103

    @property
    def holder_object(self):
        return self.archetype


class FeatureParamDef(ParamDefHolder):
    """ valid parameter paths which can be associated with this feature """

    feature_id = Column(Integer,
                        ForeignKey('feature.id',
                                   name='%s_feature_fk' % _PARAM_DEF_HOLDER,
                                   ondelete='CASCADE'),
                        nullable=True)

    feature = relation(Feature,
                       backref=backref('paramdef_holder', uselist=False,
                                       cascade='all, delete-orphan'))

    __extra_table_args__ = (UniqueConstraint(feature_id,
                                             name='param_def_holder_feature_uk'),)
    __mapper_args__ = {'polymorphic_identity': 'feature'}

    @property
    def holder_name(self):
        return "%s" % self.feature.name  # pylint: disable=C0103

    @property
    def holder_object(self):
        return self.feature


class ParamDefinition(Base):
    """
        define parameter paths
    """

    __tablename__ = _TN
    _class_label = 'Parameter Definition'
    _instance_label = 'path'

    id = Column(Integer, Sequence('%s_seq' % _TN), primary_key=True)
    path = Column(String(255), nullable=False)
    template = Column(String(32))
    required = Column(Boolean(name="%s_paramdef_ck" % _TN), default=False,
                      nullable=False)
    value_type = Column(Enum(16, _PATH_TYPES), nullable=False, default="string")
    default = Column(Text, nullable=True)
    description = deferred(Column(String(255), nullable=True))
    holder_id = Column(Integer, ForeignKey('%s.id' % _PARAM_DEF_HOLDER,
                                           name='%s_holder_fk' % _TN,
                                           ondelete='CASCADE'),
                       nullable=False)
    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    rebuild_required = Column(Boolean(name="%s_rebuild_ck" % _TN),
                              nullable=False, default=False)
    holder = relation(ParamDefHolder, innerjoin=True,
                      backref=backref('param_definitions',
                                      cascade='all, delete-orphan'))

    __table_args__ = (Index('%s_holder_idx' % _TN, holder_id),
                      {'oracle_compress': True})

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

param_definition = ParamDefinition.__table__  # pylint: disable=C0103
param_definition.info['unique_fields'] = ['path', 'holder']
