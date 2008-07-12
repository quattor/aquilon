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
import os

DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(DIR, '..'))

import depends

from sqlalchemy import (Table, Column, Integer, DateTime, Sequence, String,
                        ForeignKey, PassiveDefault, UniqueConstraint)
from sqlalchemy.orm import relation, deferred

from column_types.aqstr  import AqStr
from db_factory          import Base
from disk_type           import DiskType
from machine             import Machine

#TODO: check constraint or ColumnType for device name
#TODO: constrain capacity to non-negative
class Disk(Base):
    """ Represent physical disks in machines """
    __tablename__ = 'disk'

    id            = Column(Integer, Sequence('disk_id_seq'), primary_key = True)
    device_name   = Column(AqStr(128), nullable = False, default = '/dev/sda1')
    machine_id    = Column(Integer, ForeignKey(
        'machine.id', name = 'disk_machine_fk', ondelete='CASCADE'),
                           nullable = False)

    disk_type_id  = Column(Integer, ForeignKey(
        'disk_type.id', name = 'disk_disk_type_fk'), nullable = False)

    capacity      = Column(Integer, nullable = False, default = 36)
    creation_date = deferred(Column(DateTime, default=datetime.now))
    comments      = deferred(Column(String(255)))

    machine   = relation(Machine, backref='disks')
    disk_type = relation(DiskType, uselist = False)

disk = Disk.__table__
disk.primary_key.name = 'disk_pk'
disk.append_constraint(UniqueConstraint(
    'machine_id', 'device_name', name ='disk_mach_dev_name_uk'))

def populate(*args, **kw):
    from db_factory import db_factory, Base
    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    if 'debug' in args:
        Base.metadata.bind.echo = True
    s = dbf.session()

    disk.create(checkfirst = True)

    if Base.metadata.bind.echo == True:
        Base.metadata.bind.echo == False
