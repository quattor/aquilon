# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2012  Contributor
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
""" Configuration  Parameter data """

from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, Sequence, String,
                        ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relation, backref, deferred

from aquilon.aqdb.column_types import JSONEncodedDict, MutationDict
from aquilon.aqdb.model import Base, Personality, FeatureLink
from aquilon.exceptions_ import NotFoundException, ArgumentError
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
    def holder_name(self):
        return None

    @property
    def holder_object(self):
        return None

paramholder = ParameterHolder.__table__  # pylint: disable=C0103, E1101
paramholder.primary_key.name = '%s_pk' % _PARAM_HOLDER


class PersonalityParameter(ParameterHolder):
    """ Association of parameters with Personality """

    __mapper_args__ = {'polymorphic_identity': 'personality'}

    personality_id = Column(Integer,
                            ForeignKey('personality.id',
                                       name='%s_persona_fk' % _PARAM_HOLDER,
                                       ondelete='CASCADE'),
                            nullable=True)

    personality = relation(Personality, uselist=False,
                    backref=backref('paramholder',
                                    cascade='all, delete-orphan',
                                    uselist=False))

    @property
    def holder_name(self):
        return "%s/%s" % (self.personality.archetype.name,  # pylint: disable=C0103, E1101
                          self.personality.name)  # pylint: disable=C0103, E1101

    @property
    def holder_object(self):
        return self.personality


class FeatureLinkParameter(ParameterHolder):
    """ Parameters associated with features """

    __mapper_args__ = {'polymorphic_identity': 'featurelink'}

    featurelink_id = Column(Integer,
                            ForeignKey('feature_link.id',
                                       name='%s_featurelink_fk' % _PARAM_HOLDER,
                                       ondelete='CASCADE'),
                            nullable=True)

    featurelink = relation(FeatureLink, uselist=False,
                           backref=backref('paramholder', uselist=False,
                                           cascade='all, delete-orphan'))

    @property
    def holder_name(self):
        ret = []
        # pylint: disable=E1101
        if self.featurelink.personality:
            ret.extend([self.featurelink.personality.archetype.name,
                       self.featurelink.personality.name])
        elif self.featurelink.archetype:
            ret.append(self.featurelink.archetype.name)

        ret.append(self.featurelink.feature.name)

        return "/".join(ret)

    @property
    def holder_object(self):
        return self.featurelink

paramholder.append_constraint(UniqueConstraint('personality_id',
                                               name='param_holder_persona_uk'))
paramholder.append_constraint(UniqueConstraint('featurelink_id',
                                               name='param_holder_flink_uk'))


class Parameter(Base):
    """
        Paramter data storing individual key value pairs
    """

    __tablename__ = _TN
    __table_args__ = {'oracle_compress': True}

    id = Column(Integer, Sequence('%s_seq' % _TN), primary_key=True)
    value = Column(MutationDict.as_mutable(JSONEncodedDict))
    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments = deferred(Column(String(255), nullable=True))
    holder_id = Column(Integer, ForeignKey('%s.id' % _PARAM_HOLDER,
                                           name='%s_paramholder_fk' % _TN,
                                           ondelete='CASCADE'))

    holder = relation(ParameterHolder,
                      backref=backref('parameters',
                                      cascade='all, delete-orphan'))

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

        # ignore the leading slash
        if pparts[0] == "":
            pparts = pparts[1:]
        return pparts

    @staticmethod
    def topath(pparts):
        """
        converts dict keys to a path

        e.g [system][key] returns system/key
        """
        return PATH_SEP.join(pparts)

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

    def set_path(self,  path, value, compel=False, preclude=False):
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
            if ppart not in dref.keys():  # pylint: disable=C0103, E1101
                dref[ppart] = {}
            dref = dref[ppart]

        dref[lastnode] = value

        ## coerce mutation of parameter since sqlalchemy
        ## cannot recognize parameter change
        self.value.changed()  # pylint: disable=C0103, E1101

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

    def del_path(self, path):
        """ delete parameter specified at a path """

        if not self.value:
            raise NotFoundException("No parameter of path=%s defined." % path)
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
            self.value.changed()  # pylint: disable=C0103, E1101
        except KeyError:
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

parameter = Parameter.__table__  # pylint: disable=C0103, E1101
parameter.primary_key.name = '%s_pk' % _TN
parameter.info['unique_fields'] = ['holder']
