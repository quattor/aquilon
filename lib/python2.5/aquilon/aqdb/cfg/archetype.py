""" Archetype specifies the metaclass of the build """
from datetime import datetime
from sqlalchemy import (Column, Integer, DateTime, Sequence, String, ForeignKey,
                        UniqueConstraint)
from sqlalchemy.orm import relation, deferred

from aquilon.aqdb.base               import Base
#from aquilon.aqdb.auth.audit_info    import AuditInfo
from aquilon.aqdb.column_types.aqstr import AqStr

_ABV = 'archetype'
_PRECEDENCE = 70


class Archetype(Base):
    """ Archetype names """
    __tablename__  = _ABV

    id   = Column(Integer, Sequence('%s_id_seq'%(_ABV)), primary_key = True)
    name = Column(AqStr(32), nullable = False)
    creation_date = deferred(Column(DateTime, default = datetime.now,
                                    nullable = False))
    comments      = deferred(Column(String(255), nullable = True))

    #audit_info_id   = deferred(Column(Integer, ForeignKey(
    #        'audit_info.id', name = '%s_audit_info_fk'%(_ABV)),
    #                                  nullable = False))

    #audit_info = relation(AuditInfo)

    #def __str__(self):
    #    return str(self.name)

archetype = Archetype.__table__
table     = Archetype.__table__

table.info['abrev']      = _ABV
table.info['precedence'] = _PRECEDENCE

archetype.primary_key.name = '%s_pk'%(_ABV)
archetype.append_constraint(UniqueConstraint('name',name='%s_uk'%(_ABV)))

def populate(sess, *args, **kw):
    if len(sess.query(Archetype).all()) > 0:
        return

    for a_name in ['aquilon', 'windows', 'aurora', 'aegis', 'vm']:
        #a = Archetype(name=a_name, audit_info = kw['audit_info'])
        a = Archetype(name=a_name)
        sess.add(a)

    try:
        sess.commit()
    except Exception, e:
        sess.rollback()
        raise e


    a = sess.query(Archetype).first()
    assert(a)

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
