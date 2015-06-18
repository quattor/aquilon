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
""" Configuration  Parameter data """

from datetime import datetime
from six.moves import range  # pylint: disable=F0401

from sqlalchemy import (Column, Integer, DateTime, Sequence, ForeignKey,
                        UniqueConstraint)
from sqlalchemy.orm import relation, backref, deferred
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.ext.mutable import MutableDict

from aquilon.exceptions_ import NotFoundException, ArgumentError, InternalError
from aquilon.aqdb.column_types import JSONEncodedDict, AqStr
from aquilon.aqdb.model import (Base, PersonalityStage, ParamDefinition,
                                ParamDefHolder)

_TN = 'parameter'


class ParameterPathNotFound(Exception):
    """
    Custom exception used by the path walker.

    It does not have to carry any extra information around - the error which
    will eventually be generated should always contain the original path
    requested by the user.
    """
    pass


class Parameter(Base):
    """
    The dbobj with which this parameter is associaetd with.
    """
    __tablename__ = _TN
    _instance_label = 'holder_name'

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)
    param_def_holder_id = Column(ForeignKey(ParamDefHolder.id), nullable=False)
    value = Column(MutableDict.as_mutable(JSONEncodedDict), nullable=False)
    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    holder_type = Column(AqStr(16), nullable=False)

    param_def_holder = relation(ParamDefHolder, innerjoin=True)

    __mapper_args__ = {'polymorphic_on': holder_type}

    @property
    def holder_name(self):  # pragma: no cover
        raise InternalError("Abstract base method called")

    @property
    def holder_object(self):  # pragma: no cover
        raise InternalError("Abstract base method called")

    @staticmethod
    def feature_path(dbfeature, path):
        """
        constructs the parameter path for feature namespace
        """
        return "/".join([dbfeature.cfg_path, path])

    def path_walk(self, path, vivify=False):
        """
        Walk the path given as parameter, and return the list of intermediate
        values being walked over. If vivify is True, then non-existend nodes
        will be created as needed.

        Returned is a list of (path_part, path_value) pairs, so that
        path_value[path_part] is always the object referenced by the given path
        component. path_value is always a reference into self.value, so
        modifying path_value[path_part] modifies self.value.
        """

        # Initial conditions: path cannot be empty, and self.value is always a
        # dict.
        if not path:  # pragma: no cover
            raise InternalError("Path must not be empty")

        current = self.value
        route = []
        parts = ParamDefinition.split_path(path)

        def handle_vivify(idx, current):
            # We need to look ahead at the next path component to figure out if
            # the component to be vivified should be a leaf, a dictionary or a
            # list
            try:
                next_part = parts[idx + 1]
            except IndexError:
                # Leaf
                return None

            # Not leaf - can be either a dict or list, depending on if the next
            # path component is a number or not
            try:
                next_part = int(next_part)
            except ValueError:
                return {}

            # Ok, it's a list - only the first item in the list can be
            # auto-vifified
            if next_part != 0:
                raise ParameterPathNotFound
            return []

        # We need look-ahead for auto-vivification, so we loop over the indexes
        # rather than the list directly
        for idx in range(0, len(parts)):
            part = parts[idx]

            if isinstance(current, dict):
                if part not in current:
                    if vivify:
                        current[part] = handle_vivify(idx, current)
                    else:
                        raise ParameterPathNotFound
            elif isinstance(current, list):
                try:
                    part = int(part)
                    if part < 0:
                        raise ValueError
                except ValueError:
                    raise ArgumentError("Invalid list index '%s'." % part)
                if part > len(current):
                    raise ParameterPathNotFound
                elif part == len(current):
                    if vivify:
                        current.append(handle_vivify(idx, current))
                    else:
                        raise ParameterPathNotFound
            else:
                raise ArgumentError("Value %r cannot be indexed." % current)

            route.append((part, current))
            current = current[part]

        return route

    def get_path(self, path, compel=True):
        try:
            route = self.path_walk(path)
        except ParameterPathNotFound:
            if compel:
                raise NotFoundException("No parameter of path=%s defined." %
                                        path)
            else:
                return None

        index, value = route.pop()
        return value[index]

    def get_feature_path(self, dbfeature, path, compel=True):
        return self.get_path(Parameter.feature_path(dbfeature, path), compel)

    def set_path(self, path, value, update=False):
        try:
            route = self.path_walk(path, not update)
        except ParameterPathNotFound:
            raise NotFoundException("No parameter of path=%s defined." % path)

        index, lastvalue = route.pop()
        # We don't want to allow overwriting False or "". So we need to spell
        # out the emptiness criteria, instead of just evaluating
        # lastvalue[index] as a boolean
        if not update and not (lastvalue[index] is None or
                               (isinstance(lastvalue[index], dict) and
                                len(lastvalue[index]) == 0) or
                               (isinstance(lastvalue[index], list) and
                                len(lastvalue[index]) == 0)):
            raise ArgumentError("Parameter with path=%s already exists." % path)

        lastvalue[index] = value

        # coerce mutation of parameter since sqlalchemy
        # cannot recognize parameter change
        self.value.changed()  # pylint: disable=E1101

    def del_path(self, path, compel=True):
        try:
            route = self.path_walk(path)
        except ParameterPathNotFound:
            if compel:
                raise NotFoundException("No parameter of path=%s defined." % path)
            else:
                return

        while route:
            index, lastvalue = route.pop()
            del lastvalue[index]

            # We want to remove dictionaries which become empty, but not lists
            if isinstance(lastvalue, dict) and len(lastvalue) == 0:
                continue

            break

        # coerce mutation of parameter since sqlalchemy
        # cannot recognize parameter change
        self.value.changed()  # pylint: disable=E1101

    @staticmethod
    def flatten(data, key="", path="", flattened=None):
        if flattened is None:
            flattened = {}
        if isinstance(data, list):
            for i, item in enumerate(data):
                Parameter.flatten(item, "%d" % i, path + "/" + key,
                                  flattened)
        elif isinstance(data, dict):
            for new_key, value in data.items():
                Parameter.flatten(value, new_key, path + "/" + key,
                                  flattened)
        else:
            flattened[((path + "/") if path else "") + key] = data
        return flattened

    def copy(self):
        return self.__class__(param_def_holder=self.param_def_holder,
                              value=self.value.copy())


class PersonalityParameter(Parameter):
    """ Association of parameters with Personality """

    personality_stage_id = Column(ForeignKey(PersonalityStage.id,
                                             ondelete='CASCADE'),
                                  nullable=True, index=True)

    personality_stage = relation(PersonalityStage,
                                 backref=backref('parameters',
                                                 cascade='all, delete-orphan',
                                                 collection_class=attribute_mapped_collection('param_def_holder')))

    __mapper_args__ = {'polymorphic_identity': 'personality'}
    __extra_table_args__ = (UniqueConstraint('param_def_holder_id',
                                             'personality_stage_id'),)

    @property
    def holder_name(self):
        return self.personality_stage.qualified_name

    @property
    def holder_object(self):
        return self.personality_stage
