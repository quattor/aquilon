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

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
