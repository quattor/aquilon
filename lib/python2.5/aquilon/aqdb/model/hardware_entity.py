# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009  Contributor
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

from sqlalchemy     import (Column, Table, Integer, Sequence, ForeignKey,
                            Index, String, DateTime)
from sqlalchemy.orm import relation, deferred

from aquilon.aqdb.model import Base, Location, Model
from aquilon.aqdb.column_types.aqstr import AqStr

#valid types are machine, tor_switch_hw, chassis_hw, console_server_hw
class HardwareEntity(Base):
    __tablename__ = 'hardware_entity'

    id = Column(Integer, Sequence('hardware_entity_seq'), primary_key=True)

    hardware_entity_type = Column(AqStr(64), nullable=False)

    location_id = Column(Integer, ForeignKey('location.id',
                                            name='hw_ent_loc_fk'),
                                            nullable=False)

    model_id = Column(Integer, ForeignKey('model.id',
                                          name='hw_ent_model_fk'),
                      nullable=False)

    serial_no = Column(String(64), nullable=True)

    creation_date = deferred(Column(DateTime, default=datetime.now, nullable=False ))
    comments = deferred(Column(String(255), nullable=True))

    location = relation(Location, uselist=False)
    model = relation(Model, uselist=False)

    __mapper_args__ = {'polymorphic_on':hardware_entity_type}

    _hardware_name = 'Unnamed hardware'
    @property
    def hardware_name(self):
        return self._hardware_name

hardware_entity = HardwareEntity.__table__
hardware_entity.primary_key.name='hardware_entity_pk'
Index('hw_ent_loc_idx',  hardware_entity.c.location_id)

table = hardware_entity


