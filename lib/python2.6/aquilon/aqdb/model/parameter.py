# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013  Contributor
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

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, ForeignKey,
                        UniqueConstraint, Index)
from sqlalchemy.orm import relation, backref, deferred

from aquilon.aqdb.column_types import JSONEncodedDict, MutationDict
from aquilon.aqdb.model import Base, Personality
from aquilon.exceptions_ import NotFoundException, ArgumentError, InternalError
from aquilon.aqdb.column_types import AqStr

_TN = 'parameter'
_PARAM_HOLDER = 'param_holder'
PATH_SEP = '/'


class ParameterHolder(Base):
    """
    The dbobj with which this parameter is associaetd with.
    """
    __tablename__ = _PARAM_HOLDER
    _class_label = 'Parameter Holder'
    _instance_label = 'holder_name'

    id = Column(Integer, Sequence('%s_seq' % _PARAM_HOLDER), primary_key=True)

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

paramholder = ParameterHolder.__table__  # pylint: disable=C0103


class PersonalityParameter(ParameterHolder):
    """ Association of parameters with Personality """

    personality_id = Column(Integer,
                            ForeignKey('personality.id',
                                       name='%s_persona_fk' % _PARAM_HOLDER,
                                       ondelete='CASCADE'),
                            nullable=True)

    personality = relation(Personality, uselist=False,
                    backref=backref('paramholder',
                                    cascade='all, delete-orphan',
                                    uselist=False))

    __extra_table_args__ = (UniqueConstraint(personality_id,
                                             name='param_holder_persona_uk'),)
    __mapper_args__ = {'polymorphic_identity': 'personality'}

    @property
    def holder_name(self):
        return "%s/%s" % (self.personality.archetype.name,  # pylint: disable=C0103
                          self.personality.name)  # pylint: disable=C0103

    @property
    def holder_object(self):
        return self.personality


class Parameter(Base):
    """
        Paramter data storing individual key value pairs
    """

    __tablename__ = _TN

    id = Column(Integer, Sequence('%s_seq' % _TN), primary_key=True)
    value = Column(MutationDict.as_mutable(JSONEncodedDict))
    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = deferred(Column(String(255), nullable=True))
    holder_id = Column(Integer, ForeignKey('%s.id' % _PARAM_HOLDER,
                                           name='%s_paramholder_fk' % _TN,
                                           ondelete='CASCADE'),
                       nullable=False)

    holder = relation(ParameterHolder, innerjoin=True,
                      backref=backref('parameters',
                                      cascade='all, delete-orphan'))

    __table_args__ = (Index('%s_holder_idx' % _TN, holder_id),
                      {'oracle_compress': True})

    @staticmethod
    def tokey(path):
        """ converts path to dict keys ie. /system/key returns [system][key]"""
        parts = Parameter.path_parts(path)
        key_str = ('["' + '"]["'.join(parts) + '"]')
        return key_str

    @staticmethod
    def path_parts(path):
        """
        converts parts of a specified path

        e.g path:/system/foo returns ['system','foo']
        """
        pparts = path.split(PATH_SEP)

        # ignore the leading and trailing slash
        if pparts[0] == "":
            pparts = pparts[1:]
        if pparts[-1] == "":
            pparts = pparts[:-1]
        return pparts

    @staticmethod
    def topath(pparts):
        """
        converts dict keys to a path

        e.g [system][key] returns system/key
        """
        return PATH_SEP.join(pparts)

    @staticmethod
    def feature_path(featurelink, path):
        """
        constructs the parameter path for feature namespace
        """
        return PATH_SEP.join([featurelink.cfg_path, path])

    def get_path(self, path, compel=True, preclude=False):
        """ get value of paramter specified by path made of dict keys """

        ref = self.value
        try:
            parts = Parameter.path_parts(path)
            for part in parts:
                ref = ref[part]
            if ref is not None:
                if preclude:
                    raise ArgumentError("Parameter with path=%s already exists."
                                        % path)
                return ref
        except KeyError:
            if compel:
                raise NotFoundException(
                      "No parameter of path=%s defined." % path)
            else:
                pass
        return None

    def get_feature_path(self, dbfeaturelink, path, compel=True, preclude=False):
        return self.get_path(Parameter.feature_path(dbfeaturelink, path),
                             compel, preclude)

    def set_path(self, path, value, compel=False, preclude=False):
        """
        add/or update a new parameter key

        value in dict specified by path made of dict keys
        """

        self.get_path(path, compel, preclude)

        pparts = Parameter.path_parts(path)
        lastnode = pparts.pop()

        ## traverse the given path to add the given value
        ## we need to know the lastnode so we can appropriately
        ## associate a string value or json value

        dref = self.value
        for ppart in pparts:
            if ppart not in dref.keys():  # pylint: disable=E1101
                dref[ppart] = {}
            dref = dref[ppart]

        dref[lastnode] = value

        ## coerce mutation of parameter since sqlalchemy
        ## cannot recognize parameter change
        self.value.changed()  # pylint: disable=E1101

    def __del_path(self, path):
        """ method to do the actual deletion """

        pparts = Parameter.path_parts(path)
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

        pparts = Parameter.path_parts(path)
        try:
            ## delete the specified path
            self.__del_path(path)

            ## after deleting the leaf check if the parent node is empty
            ## if so delete it
            while pparts.pop():
                if not pparts:
                    break
                newpath = Parameter.topath(pparts)
                if self.get_path(newpath):
                    break
                self.__del_path(newpath)

            ## coerce mutation of parameter since sqlalchemy
            ## cannot recognize parameter change
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
                Parameter.flatten(item, "%d" % i, path + PATH_SEP + key,
                                  flattened)
        elif isinstance(data, dict):
            for new_key, value in data.items():
                Parameter.flatten(value, new_key, path + PATH_SEP + key,
                                  flattened)
        else:
            flattened[((path + PATH_SEP) if path else "") + key] = data
        return flattened

parameter = Parameter.__table__  # pylint: disable=C0103
parameter.info['unique_fields'] = ['holder']
