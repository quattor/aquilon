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
"""The tables/objects/mappings related to hardware in Aquilon. """

from datetime import datetime

from sqlalchemy import (UniqueConstraint, Table, Column, Integer, DateTime,
                        Sequence, String, ForeignKey, Index)

from sqlalchemy.orm  import relation, deferred, backref

from aquilon.aqdb.column_types.aqstr import AqStr

from aquilon.aqdb.model import Cpu, CfgPath, HardwareEntity

#TODO: use selection of the machine specs to dynamically populate default
#     values for all of the attrs where its possible

class Machine(HardwareEntity):
    __tablename__ = 'machine'
    __mapper_args__ = {'polymorphic_identity' : 'machine'}

    #hardware_entity_
    machine_id = Column(Integer, ForeignKey('hardware_entity.id',
                                           name='machine_hw_ent_fk'),
                                           primary_key=True)

    name = Column('name', AqStr(64), nullable=False)

    cpu_id = Column(Integer, ForeignKey(
        'cpu.id', name='machine_cpu_fk'), nullable=False)

    cpu_quantity = Column(Integer, nullable=False, default=2) #constrain/smallint

    memory = Column(Integer, nullable=False, default=512)

    hardware_entity = relation(HardwareEntity, uselist=False,
                               backref='machine')

    cpu = relation(Cpu, uselist=False)

    #TODO: synonym in location/model?
    #location = relation(Location, uselist=False)

    @property
    def hardware_name(self):
        return self.name

machine = Machine.__table__

machine.primary_key.name='machine_pk'

machine.append_constraint(
    UniqueConstraint('name',name='machine_name_uk')
)

table = machine

#TODO:
#   check if it exists in dbdb minfo, and get from there if it does
#   and/or -dsdb option, and, make machine --like [other machine] + overrides
