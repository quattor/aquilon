""" Enumerates kerberos realms """
from datetime import datetime

from sqlalchemy import (Column, Integer, String, DateTime, Sequence, ForeignKey,
                        UniqueConstraint)

from sqlalchemy.orm                  import relation, deferred

from aquilon.aqdb.base               import Base
from aquilon.aqdb.column_types.aqstr import AqStr

#Upfront Design Decisions:
#  -Needs it's own creation_date + comments columns. Audit log depends on
#   this table for it's info, and would have a circular dependency
_PRECEDENCE = 10

class Realm(Base):
    __tablename__ = 'realm'

    id = Column(Integer, Sequence('realm_seq'), primary_key = True)

    name = Column(AqStr(32), nullable = False)

    creation_date = deferred(Column(DateTime,
                                    nullable=False, default=datetime.now))

    comments = deferred(Column('comments', String(255), nullable=True))

realm = Realm.__table__
table = Realm.__table__

table.info['precedence'] = _PRECEDENCE

realm.append_constraint(UniqueConstraint('name',name='realm_uk'))

def populate(sess, *args, **kw):
    if sess.query(Realm).count() == 0:
        r = Realm(name = 'is1.morgan')
        sess.add(r)
        sess.commit()
        r = sess.query(Realm).first()
        assert(r)
    else:
        return True

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
