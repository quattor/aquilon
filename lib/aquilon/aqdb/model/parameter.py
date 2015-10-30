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

from sqlalchemy import Column, Integer, DateTime, Sequence, ForeignKey
from sqlalchemy.orm import relation, backref, deferred
from sqlalchemy.ext.mutable import MutableDict

from aquilon.exceptions_ import NotFoundException, ArgumentError, InternalError
from aquilon.aqdb.column_types import JSONEncodedDict, AqStr
from aquilon.aqdb.model import Base, PersonalityStage, ParamDefinition

_TN = 'parameter'


class Parameter(Base):
    """
    The dbobj with which this parameter is associaetd with.
    """
    __tablename__ = _TN
    _instance_label = 'holder_name'

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)
    value = Column(MutableDict.as_mutable(JSONEncodedDict), nullable=False)
    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    holder_type = Column(AqStr(16), nullable=False)

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

    def get_path(self, path, compel=True, preclude=False):
        """ get value of paramter specified by path made of dict keys """

        ref = self.value
        try:
            parts = ParamDefinition.split_path(path)
            for part in parts:
                ref = ref[part]
            if ref is not None:
                if preclude:
                    raise ArgumentError("Parameter with path=%s already exists."
                                        % path)
                return ref
        except KeyError:
            if compel:
                raise NotFoundException("No parameter of path=%s defined." %
                                        path)
            else:
                pass
        return None

    def get_feature_path(self, dbfeature, path, compel=True, preclude=False):
        return self.get_path(Parameter.feature_path(dbfeature, path),
                             compel, preclude)

    def set_path(self, path, value, compel=False, preclude=False):
        """
        add/or update a new parameter key

        value in dict specified by path made of dict keys
        """

        self.get_path(path, compel, preclude)

        pparts = ParamDefinition.split_path(path)
        lastnode = pparts.pop()

        # traverse the given path to add the given value
        # we need to know the lastnode so we can appropriately
        # associate a string value or json value

        dref = self.value
        for ppart in pparts:
            if ppart not in dref:
                dref[ppart] = {}
            dref = dref[ppart]

        dref[lastnode] = value

        # coerce mutation of parameter since sqlalchemy
        # cannot recognize parameter change
        self.value.changed()  # pylint: disable=E1101

    def __del_path(self, path):
        """ method to do the actual deletion """

        pparts = ParamDefinition.split_path(path)
        lastnode = pparts.pop()
        dref = self.value
        try:
            for ppart in pparts:
                dref = dref[ppart]
            del dref[lastnode]
        except KeyError:
            raise NotFoundException("No parameter of path=%s defined." % path)

    def del_path(self, path, compel=True):
        """ delete parameter specified at a path """

        if not self.value:
            if compel:
                raise NotFoundException("No parameter of path=%s defined." % path)
            return

        pparts = ParamDefinition.split_path(path)
        try:
            # delete the specified path
            self.__del_path(path)

            # after deleting the leaf check if the parent node is empty
            # if so delete it
            while pparts.pop():
                if not pparts:
                    break
                newpath = "/".join(pparts)
                if self.get_path(newpath):
                    break
                self.__del_path(newpath)

            # coerce mutation of parameter since sqlalchemy
            # cannot recognize parameter change
            self.value.changed()  # pylint: disable=E1101
        except:
            if compel:
                raise NotFoundException("No parameter of path=%s defined." % path)

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
        return self.__class__(value=self.value.copy())


class PersonalityParameter(Parameter):
    """ Association of parameters with Personality """

    personality_stage_id = Column(ForeignKey(PersonalityStage.id,
                                             ondelete='CASCADE'),
                                  nullable=True, unique=True)

    personality_stage = relation(PersonalityStage,
                                 backref=backref('parameter', uselist=False,
                                                 cascade='all, delete-orphan'))

    __mapper_args__ = {'polymorphic_identity': 'personality'}

    @property
    def holder_name(self):
        return self.personality_stage.qualified_name

    @property
    def holder_object(self):
        return self.personality_stage
