#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrapper to make getting a disk_type simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.hw.disk_type import DiskType


def get_disk_type(session, disk_type):
    try:
        dbdisk_type = session.query(DiskType).filter_by(type=disk_type).one()
    except InvalidRequestError, e:
        raise NotFoundException("DiskType %s not found: %s" % (disk_type, e))
    return dbdisk_type


#if __name__=='__main__':
