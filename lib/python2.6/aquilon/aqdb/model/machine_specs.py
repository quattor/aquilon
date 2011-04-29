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
""" Machine Specifications: the rows of this table represent the default
    values of machine "models" so that users don't need to manaully enter the
    low level details of each one since this is mostly repeated data in large
    grid deployments, such as Saphire """

from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, ForeignKey,
                        UniqueConstraint)
from sqlalchemy.orm import relation, backref

from aquilon.aqdb.column_types import Enum
from aquilon.aqdb.model import Base, Model, Cpu
from aquilon.aqdb.model.disk import disk_types, controller_types


class MachineSpecs(Base):
    """ Captures the configuration hardware components for a given model """
    #TODO: Maybe this entire table is in fact a part of the model "subtype"

    _def_cpu_cnt = {'workstation': 1, 'blade': 2, 'rackmount': 4}
    _def_nic_cnt = {'workstation': 1, 'blade': 2, 'rackmount': 2}
    _def_memory = {'workstation': 2048, 'blade': 8192, 'rackmount': 16384}

    __tablename__ = 'machine_specs'
    id = Column(Integer, Sequence('mach_specs_id_seq'), primary_key=True)

    model_id = Column(Integer, ForeignKey('model.id',
                                          name='mach_spec_model_fk'),
                      nullable=False)

    cpu_id = Column(Integer, ForeignKey('cpu.id',
                                        name='mach_spec_cpu_fk'),
                    nullable=False)

    cpu_quantity = Column(Integer, nullable=False)  # Constrain to below 512?

    memory = Column(Integer, nullable=False, default=0)

    disk_type = Column(Enum(64, disk_types), nullable=False)
    disk_capacity = Column(Integer, nullable=False, default=36)
    controller_type = Column(Enum(64, controller_types), nullable=False)

    nic_count = Column(Integer, nullable=False, default=2)

    creation_date = Column('creation_date', DateTime, default=datetime.now)
    comments = Column('comments', String(255), nullable=True)

    model = relation(Model, innerjoin=True,
                     backref=backref('machine_specs', uselist=False))
    cpu = relation(Cpu, innerjoin=True)

    @property
    def disk_name(self):
        if self.controller_type == 'cciss':
            return 'c0d0'
        return 'sda'


machine_specs = MachineSpecs.__table__  # pylint: disable-msg=C0103, E1101
machine_specs.primary_key.name = 'machine_specs_pk'

#for now, need a UK on model_id. WILL be a name AND a model_id as UK.
machine_specs.append_constraint(
    UniqueConstraint('model_id', name='machine_specs_model_uk'))
