#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Individual, physical disks """
from datetime import datetime
import sys
sys.path.insert(0,'..')
sys.path.insert(1,'../..')
sys.path.insert(2,'../../..')

import depends
from sqlalchemy import (Table, Column, Integer, DateTime, Sequence, String,
                        ForeignKey, PassiveDefault, UniqueConstraint)
from sqlalchemy.orm import relation, deferred

from db import Base
from disk_type import DiskType, disk_type
from machine import Machine, machine

class Disk(Base):
    __tablename__ = 'disk'
    id = Column(Integer, Sequence('disk_id_seq'), primary_key=True)
    device_name = Column(String(32), nullable=False, default='/dev/sda1')
    machine_id = Column(Integer, ForeignKey('machine.id', ondelete='CASCADE'),
                        nullable=False)
    disk_type_id = Column(Integer, ForeignKey('disk_type.id'), nullable = False)
    capacity = Column(Integer, nullable = False) #TODO: constrain non-negative
    creation_date = deferred(Column(DateTime, default=datetime.now))
    comments = deferred(Column(String(255)))

    machine = relation(Machine,backref='disks')
    type    = relation(DiskType)

disk = Disk.__table__
disk.primary_key.name = 'disk_pk'
#TODO: need a device name + unique constraint
