# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012  Contributor
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

    personality_id = Column(Integer, ForeignKey("personality.id",
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

    __mapper_args__ = {'polymorphic_on': cluster_type}

pci = PersonalityClusterInfo.__table__  # pylint: disable=C0103
pci.primary_key.name = "%s_pk" % _PCIABV
pci.append_constraint(UniqueConstraint("personality_id", "cluster_type",
                                       name="%s_pc_uk" % _PCIABV))


class PersonalityESXClusterInfo(PersonalityClusterInfo):
    """ Extra personality data specific to ESX clusters """

    __tablename__ = _PECI
    __mapper_args__ = {'polymorphic_identity': 'esx'}

    personality_cluster_info_id = Column(Integer,
                                         ForeignKey("%s.id" % _PCI,
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
