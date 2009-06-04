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
""" Individual, physical disks """

from datetime import datetime

from sqlalchemy import (Table, Column, Integer, DateTime, Sequence, String,
                        ForeignKey, PassiveDefault, UniqueConstraint)
from sqlalchemy.orm import relation, deferred


from aquilon.aqdb.model import Base, DiskType, Machine
from aquilon.aqdb.column_types.aqstr import AqStr


#TODO: check constraintraint or ColumnType for device name
#TODO: constrain capacity to non-negative
class Disk(Base):
    """ Represent physical disks in machines """
    __tablename__ = 'disk'

    id = Column(Integer, Sequence('disk_id_seq'), primary_key=True)
    device_name = Column(AqStr(128), nullable=False, default = 'sda')

    machine_id = Column(Integer, ForeignKey('machine.machine_id',
                                            name='disk_machine_fk',
                                            ondelete='CASCADE'),
                        nullable=False)

    disk_type_id = Column(Integer, ForeignKey('disk_type.id',
                                               name='disk_disk_type_fk'),
                           nullable=False)

    capacity = Column(Integer, nullable=False, default = 36)
    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False ))
    comments = deferred(Column(String(255)))

    machine = relation(Machine, backref='disks', passive_deletes=True)
    disk_type = relation(DiskType, uselist=False)

disk = Disk.__table__
disk.primary_key.name='disk_pk'
disk.append_constraint(UniqueConstraint('machine_id', 'device_name',
                                        name='disk_mach_dev_name_uk'))

table = disk


