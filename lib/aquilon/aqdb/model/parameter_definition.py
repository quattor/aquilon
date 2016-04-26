# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013,2014,2015  Contributor
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
import json
from jsonschema import validate, ValidationError, Draft4Validator
import re

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, Boolean,
                        Text, ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relation, backref, deferred, validates
from sqlalchemy.orm.collections import column_mapped_collection

from aquilon.exceptions_ import ArgumentError, InternalError
from aquilon.aqdb.column_types import AqStr, EmptyStr, Enum, JSONEncodedDict
from aquilon.aqdb.model import Base, Archetype, Feature
from aquilon.aqdb.model.feature import _ACTIVATION_TYPE
from aquilon.utils import (force_json, force_int, force_float, force_boolean,
                           validate_nlist_key)

_TN = 'param_definition'
_PARAM_DEF_HOLDER = 'param_def_holder'
_PATH_TYPES = ['list', 'string', 'int', 'float', 'boolean', 'json']
_PATH_RE = re.compile(r'/+')


class ParamDefHolder(Base):
    """
    The dbobj with which this parameter paths are  associated with.
    """
    __tablename__ = _PARAM_DEF_HOLDER
    _class_label = 'Parameter Definition Holder'
    _instance_label = 'holder_name'

    id = Column(Integer, Sequence('%s_id_seq' % _PARAM_DEF_HOLDER), primary_key=True)

    type = Column(AqStr(16), nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    __mapper_args__ = {'polymorphic_on': type,
                       'with_polymorphic': '*'}

    @property
    def holder_name(self):  # pragma: no cover
        raise InternalError("Abstract base method called")

    @property
    def holder_object(self):  # pragma: no cover
        raise InternalError("Abstract base method called")

    def check_new_path(self, path):
        # path is expected to be normalized
        for db_paramdef in self.param_definitions:
            if path == db_paramdef.path or \
               not path or not db_paramdef.path or \
               path.startswith(db_paramdef.path + "/") or \
               db_paramdef.path.startswith(path + "/"):
                raise ArgumentError("The path cannot be a strict subset or "
                                    "superset of an existing definition.")


class ArchetypeParamDef(ParamDefHolder):
    """ valid parameter paths which can be associated with this archetype """

    __mapper_args__ = {'polymorphic_identity': 'archetype'}

    archetype_id = Column(ForeignKey(Archetype.id, ondelete='CASCADE'),
                          nullable=True)

    template = Column(String(32))

    archetype = relation(Archetype,
                         backref=backref('param_def_holders',
                                         cascade='all, delete-orphan',
                                         passive_deletes=True,
                                         collection_class=column_mapped_collection(template)))

    __extra_table_args__ = (UniqueConstraint(archetype_id, template,
                                             name="%s_arch_tmpl_uk" % _PARAM_DEF_HOLDER),)

    @property
    def holder_name(self):
        return "%s" % self.archetype.name  # pylint: disable=C0103

    @property
    def holder_object(self):
        return self.archetype


class FeatureParamDef(ParamDefHolder):
    """ valid parameter paths which can be associated with this feature """

    feature_id = Column(ForeignKey(Feature.id, ondelete='CASCADE'),
                        nullable=True, unique=True)

    feature = relation(Feature,
                       backref=backref('param_def_holder', uselist=False,
                                       cascade='all, delete-orphan',
                                       passive_deletes=True))

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

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)
    path = Column(EmptyStr(255), nullable=False)
    required = Column(Boolean(name="%s_required_ck" % _TN), default=False,
                      nullable=False)
    value_type = Column(Enum(16, _PATH_TYPES), nullable=False, default="string")
    schema = Column(JSONEncodedDict, nullable=True)
    default = Column(Text, nullable=True)
    description = deferred(Column(String(255), nullable=True))
    holder_id = Column(ForeignKey(ParamDefHolder.id, ondelete='CASCADE'),
                       nullable=False, index=True)
    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    activation = Column(Enum(10, _ACTIVATION_TYPE), nullable=True)

    holder = relation(ParamDefHolder, innerjoin=True,
                      backref=backref('param_definitions',
                                      cascade='all, delete-orphan'))

    __table_args__ = ({'oracle_compress': True,
                       'info': {'unique_fields': ['path', 'holder']}},)

    @staticmethod
    def split_path(path):
        # Ignore leading and trailing slashes, collapse multiple slashes into one
        return [part for part in path.split("/") if part]

    @staticmethod
    def normalize_path(path, strict=True):
        parts = ParamDefinition.split_path(path)
        # Normally, we want all path components to be valid. However, deleting
        # an invalid path which somehow got there could turn out to be useful,
        # so there's a way to turn stict verification off.
        if strict:
            for part in parts:
                validate_nlist_key("a path component", part)
        else:
            validate_nlist_key("a path component", parts[0])
        return "/".join(parts)

    @validates('path')
    def validate_path(self, key, value):  # pylint: disable=W0613
        return self.normalize_path(value)

    @validates('value_type')
    def validate_value_type(self, key, value):  # pylint: disable=W0613
        """ Utility function for validating the value type """
        if value in _PATH_TYPES:
            return value
        valid_types = ", ".join(sorted(_PATH_TYPES))
        raise ArgumentError("Unknown value type '%s'.  The valid types are: "
                            "%s." % (value, valid_types))

    @validates('default')
    def validate_default(self, key, value):  # pylint: disable=W0613
        if value is None:
            return None

        retval = self.parse_value("default for path=%s" % self.path, value)
        if self.schema:
            try:
                validate(retval, self.schema)
            except ValidationError as err:
                raise ArgumentError(err)

        # Ensure JSON defaults get stored in a normalized form
        if self.value_type == "json":
            return json.dumps(retval, sort_keys=True)
        else:
            return value

    @validates('schema')
    def validate_schema(self, key, value):  # pylint: disable=W0613
        if value is None:
            return value
        Draft4Validator.check_schema(value)

        if self.default:
            try:
                validate(json.loads(self.default), value)
            except ValidationError as err:
                raise ArgumentError("The existing default value conflicts "
                                    "with the new schema: %s" % err)
        return value

    @validates('activation')
    def validate_activation(self, key, activation):
        """ Utility function for validating the value type """
        if activation in _ACTIVATION_TYPE or activation is None:
            return activation
        valid_activation = ", ".join(sorted(_ACTIVATION_TYPE))
        raise ArgumentError("Unknown value for %s. Valid values are: "
                            "%s." % (key, valid_activation))

    @property
    def parsed_default(self):
        if self.default is None:
            return None

        return self.parse_value("default for path=%s" % self.path, self.default)

    def parse_value(self, label, value):
        if self.value_type == 'string':
            return value
        elif self.value_type == 'list':
            return [item.strip() for item in value.split(",")]
        elif self.value_type == 'int':
            return force_int(label, value)
        elif self.value_type == 'float':
            return force_float(label, value)
        elif self.value_type == 'boolean':
            return force_boolean(label, value)
        elif self.value_type == 'json':
            # Note: do not try to validate the schema here - "value" may be just
            # a small fragment of the value associated with this parameter
            # definition
            try:
                return force_json(label, value)
            except ArgumentError:
                # Usability improvement: accept bare strings which do not
                # contain any special characters interpreted by the JSON
                # decoder. This should allow e.g. usernames or file names.
                if re.match(r"^[a-zA-Z_/][a-zA-Z0-9_/.-]*$", value):
                    return value
                raise

        raise InternalError("Unhandled type: %s" % self.value_type)
