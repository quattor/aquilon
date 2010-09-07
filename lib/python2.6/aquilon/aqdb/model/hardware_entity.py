# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
""" Base class of polymorphic hardware structures """
from datetime import datetime

from sqlalchemy import (Column, Integer, Sequence, ForeignKey, UniqueConstraint,
                        Index, String, DateTime)
from sqlalchemy.orm import relation

from aquilon.aqdb.model import Base, Location, Model
from aquilon.aqdb.column_types import AqStr, Enum

HARDWARE_TYPES = ['machine', 'switch', 'chassis']  # , 'netapp_filer']
_TN = "hardware_entity"


class HardwareEntity(Base):  # pylint: disable-msg=W0232, R0903
    __tablename__ = _TN
    _instance_label = 'label'

    id = Column(Integer, Sequence('%s_seq' % _TN), primary_key=True)

    label = Column(AqStr(63), nullable=False)

    hardware_type = Column(Enum(64, HARDWARE_TYPES), nullable=False)

    location_id = Column(Integer, ForeignKey('location.id',
                                            name='hw_ent_loc_fk'),
                         nullable=False)

    model_id = Column(Integer, ForeignKey('model.id',
                                          name='hw_ent_model_fk'),
                      nullable=False)

    serial_no = Column(String(64), nullable=True)

    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments = Column(String(255), nullable=True)

    location = relation(Location, uselist=False)
    model = relation(Model, uselist=False)

    __mapper_args__ = {'polymorphic_on': hardware_type}

hardware_entity = HardwareEntity.__table__
hardware_entity.primary_key.name = '%s_pk' % _TN
hardware_entity.append_constraint(UniqueConstraint('label', name='%s_label_uk' % _TN))
hardware_entity.info['unique_fields'] = ['label']
Index('hw_ent_loc_idx',  hardware_entity.c.location_id)
