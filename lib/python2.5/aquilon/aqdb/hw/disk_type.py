""" For the various types of disks we use """

from aquilon.aqdb.table_types.subtype import subtype

DiskType = subtype('DiskType','disk_type','Disk Type: scsi, cciss, sata, etc.')
disk_type = DiskType.__table__
disk_type.primary_key.name = 'disk_type_pk'

table = disk_type

_disk_types = ['cciss', 'ide', 'sas', 'sata', 'scsi', 'flash']

def populate(sess, *args, **kw):
    if len(sess.query(DiskType).all()) < 1:
        for t in _disk_types:
            dt = DiskType(type = t, comments = 'AutoPopulated')
            sess.add(dt)
        sess.commit()

    dt = sess.query(DiskType).first()
    assert(dt)

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
