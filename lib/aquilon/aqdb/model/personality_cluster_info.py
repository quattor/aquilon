# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013,2014  Contributor
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
""" Extra cluster-specific information about a personality """

from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, ForeignKey,
                        Float, UniqueConstraint)
from sqlalchemy.orm import relation, backref, reconstructor, deferred
from sqlalchemy.orm.collections import column_mapped_collection

from aquilon.aqdb.model import Base, Personality
from aquilon.aqdb.column_types.aqstr import AqStr

_PCI = "personality_cluster_info"
_PCIABV = "pers_clst_info"
_PECI = "personality_esx_cluster_info"
_PECIABV = "pers_esxcl_info"


class PersonalityClusterInfo(Base):
    """ Extra personality data specific to clusters """

    __tablename__ = _PCI

    id = Column(Integer, Sequence("%s_seq" % _PCIABV), primary_key=True)

    personality_id = Column(Integer, ForeignKey(Personality.id,
                                                name="%s_pers_fk" % _PCIABV,
                                                ondelete="CASCADE"),
                            nullable=False)
    cluster_type = Column(AqStr(16), nullable=False)

    personality = relation(Personality, lazy=False,
                           innerjoin=True,
                           backref=backref("cluster_infos",
                                           collection_class=column_mapped_collection(cluster_type),
                                           cascade="all"))

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    __table_args__ = (UniqueConstraint(personality_id, cluster_type,
                                       name="%s_pc_uk" % _PCIABV),)
    __mapper_args__ = {'polymorphic_on': cluster_type}

pci = PersonalityClusterInfo.__table__  # pylint: disable=C0103
pci.primary_key.name = "%s_pk" % _PCIABV


class PersonalityESXClusterInfo(PersonalityClusterInfo):
    """ Extra personality data specific to ESX clusters """

    __tablename__ = _PECI
    __mapper_args__ = {'polymorphic_identity': 'esx'}

    personality_cluster_info_id = Column(Integer,
                                         ForeignKey(PersonalityClusterInfo.id,
                                                    name="%s_pci_fk" % _PECIABV,
                                                    ondelete="CASCADE"),
                                         primary_key=True)

    _vmhost_capacity_function = Column('vmhost_capacity_function', String(255),
                                       nullable=True)

    vmhost_overcommit_memory = Column(Float, nullable=False, default=1.0)

    # A little trickery here, as we want to cache the compiled function
    @property
    def vmhost_capacity_function(self):
        return self._vmhost_capacity_function

    @vmhost_capacity_function.setter
    def vmhost_capacity_function(self, value):
        self._vmhost_capacity_function = value
        self._compiled_vmhost = None

    @property
    def compiled_vmhost_capacity_function(self):
        if self._compiled_vmhost:
            return self._compiled_vmhost
        if self._vmhost_capacity_function:
            func = compile(self._vmhost_capacity_function, "<string>", "eval")
        else:
            # TODO Get it from the configuration?
            func = None
        self._compiled_vmhost = func
        return func

    @reconstructor
    def setup(self):
        # Loading an object from the DB does not call __init__
        self._compiled_vmhost = None

    def __init__(self, **kwargs):
        super(PersonalityESXClusterInfo, self).__init__(**kwargs)
        self._compiled_vmhost = None

pcei = PersonalityESXClusterInfo.__table__  # pylint: disable=C0103
pcei.primary_key.name = "%s_pk" % _PECIABV
