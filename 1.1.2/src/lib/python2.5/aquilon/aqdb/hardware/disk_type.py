#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
import sys
sys.path.insert(0,'..')
sys.path.insert(1,'../..')
sys.path.insert(2,'../../..')

from subtypes import subtype

DiskType = subtype('DiskType','disk_type', 'Disk Type: scsi, ccis, sata, etc.')
disk_type = DiskType.__table__

def populate_disk_type():
    if empty(disk_type):
        print 'Populating disk_types... ',
        import configuration as cfg
        from aquilon import const
        d=os.path.join(const.cfg_base,'hardware/harddisk/generic')
        disk_types=[]
        for i in os.listdir(d):
            disk_types.append(os.path.splitext(i)[0])
        fill_type_table(disk_type,disk_types)
        print '%s'%(disk_types)
