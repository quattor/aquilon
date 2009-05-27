""" Contains tables and objects for authorization in Aquilon """
from datetime import datetime

from sqlalchemy import (Column, Integer, String, DateTime, Sequence, ForeignKey,
                        UniqueConstraint)

from sqlalchemy.orm import relation, deferred

from aquilon.aqdb.model import Base
from aquilon.aqdb.column_types.aqstr import AqStr

#Upfront Design Decisions:
#  -Needs it's own creation_date + comments columns. Audit log depends on
#   this table for it's info, and would have a circular dependency
_PRECEDENCE = 10

class Role(Base):
    __tablename__ = 'role'

    id = Column(Integer, Sequence('role_seq'), primary_key = True)

    name = Column(AqStr(32), nullable = False)

    creation_date = deferred(Column(DateTime,
                                    nullable=False, default=datetime.now))

    comments = deferred(Column('comments', String(255), nullable=True))

role  = Role.__table__
table = Role.__table__

table.info['precedence'] = _PRECEDENCE

role.primary_key.name = 'role_pk'
role.append_constraint(UniqueConstraint('name',name='role_uk'))

def populate(sess, *args, **kw):
    roles = ['nobody', 'operations', 'engineering', 'aqd_admin', 'telco_eng']

    if sess.query(Role).count() >= len(roles):
        return

    for i in roles:
        r=Role(name = i)
        sess.add(r)

    try:
        sess.flush()
    except Exception, e:
        sess.rollback()
        raise e

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon
