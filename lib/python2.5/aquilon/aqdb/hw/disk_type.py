#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" For the various types of disks we use """

import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from aquilon.aqdb.table_types.subtype import subtype

DiskType = subtype('DiskType','disk_type','Disk Type: scsi, ccis, sata, etc.')
disk_type = DiskType.__table__
disk_type.primary_key.name = 'disk_type_pk'

table = disk_type

_disk_types = ['ccis', 'ide', 'sas', 'sata', 'scsi', 'flash']

def populate(db, *args, **kw):
    if len(db.s.query(DiskType).all()) < 1:
        for t in _disk_types:
            dt = DiskType(type = t, comments = 'AutoPopulated')
            db.s.add(dt)
        db.s.commit()

    dt = db.s.query(DiskType).first()
    assert(dt)

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
