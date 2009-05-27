""" Status is an overloaded term, but we use it to represent various stages of
    deployment, such as production, QA, dev, etc. each of which are also
    overloaded terms... """
from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, ForeignKey,
                        UniqueConstraint)

#from sqlalchemy.orm import relation

from aquilon.aqdb.model import Base
from aquilon.aqdb.column_types.aqstr import AqStr
#from aquilon.aqdb.auth.audit_info    import AuditInfo

_ABV = 'status'
_PRECEDENCE = 50
_statuses = ['blind', 'build', 'ready']

class Status(Base):
    """ Status names """
    __tablename__  = _ABV

    id   = Column(Integer, Sequence('%s_id_seq'%(_ABV)), primary_key=True)
    name = Column(AqStr(32), nullable=False)
    creation_date = Column(DateTime, default = datetime.now,
                                    nullable = False )
    comments      = Column(String(255), nullable = True)

#    audit_info_id   = deferred(Column(Integer, ForeignKey(
#            'audit_info.id', name = '%s_audit_info_fk'%(_ABV)),
#                                      nullable = False))

#    audit_info = relation(AuditInfo)

    def __init__(self,name):
        e = "Status is a static table and can't be instanced, only queried."
        raise ValueError(e)

    def __repr__(self):
        return str(self.name)

status = Status.__table__
table  = Status.__table__

table.info['abrev']      = _ABV
table.info['precedence'] = _PRECEDENCE

status.primary_key.name = '%s_pk'%(_ABV)
status.append_constraint(UniqueConstraint('name',name='%s_uk'%(_ABV)))


def populate(sess, *args, **kw):
    from sqlalchemy import insert
    from sqlalchemy.exceptions import IntegrityError
    #ai_id = kw['audit_info'].id

    if len(sess.query(Status).all()) < len(_statuses):
        i=status.insert()
        for name in _statuses:
            try:
                i.execute(name=name)#), audit_info_id=ai_id)
            except IntegrityError:
                pass

    assert len(sess.query(Status).all()) == len(_statuses)

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
