""" For the various types of disks we use """
from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, ForeignKey,
                        UniqueConstraint)
from sqlalchemy.orm import relation

from aquilon.aqdb.base               import Base
from aquilon.aqdb.column_types.aqstr import AqStr
#from aquilon.aqdb.auth.audit_info    import AuditInfo

_ABV = 'disk_type'
_PRECEDENCE = 50
_disk_types = ['cciss', 'ide', 'sas', 'sata', 'scsi', 'flash']


class DiskType(Base):
    """ Disk Type: scsi, cciss, sata, etc. """
    __tablename__  = _ABV

    id   = Column(Integer, Sequence('%s_seq'%(_ABV)), primary_key = True)
    type = Column(AqStr(32), nullable = False)

    creation_date = Column(DateTime, default = datetime.now, nullable = False)
    comments      = Column(String(255), nullable = True)

    #audit_info_id   = deferred(Column(Integer, ForeignKey(
    #        'audit_info.id', name = '%s_audit_info_fk'%(_ABV)),
    #                                  nullable = False))

    #audit_info = relation(AuditInfo)

    #def __str__(self):
    #    return str(self.typ)

disk_type = DiskType.__table__
table     = DiskType.__table__

table.info['abrev']      = _ABV
table.info['precedence'] = _PRECEDENCE

disk_type.primary_key.name = '%s_pk'%(_ABV)
disk_type.append_constraint(UniqueConstraint('type',name='%s_uk'%(_ABV)))


def populate(sess, *args, **kw):
    if len(sess.query(DiskType).all()) < 1:
        for t in _disk_types:
            dt = DiskType(type = t)#, audit_info=kw['audit_info'])
            sess.add(dt)
        try:
            sess.commit()
        except Exception, e:
            sess.rollback()
            raise e

    dt = sess.query(DiskType).first()
    assert(dt)

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
