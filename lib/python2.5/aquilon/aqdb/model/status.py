""" Status is an overloaded term, but we use it to represent various stages of
    deployment, such as production, QA, dev, etc. each of which are also
    overloaded terms... """
from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, ForeignKey,
                        UniqueConstraint)

from aquilon.aqdb.model import Base
from aquilon.aqdb.column_types.aqstr import AqStr

_statuses = ['blind', 'build', 'ready']

_TN = 'status'

class Status(Base):
    """ Status names """
    __tablename__  = _TN

    id = Column(Integer, Sequence('%s_id_seq'%(_TN)), primary_key=True)
    name = Column(AqStr(32), nullable=False)
    creation_date = Column(DateTime, default=datetime.now,
                                    nullable=False )
    comments = Column(String(255), nullable=True)

    def __init__(self,name):
        e = "Status is a static table and can't be instanced, only queried."
        raise ValueError(e)

    def __repr__(self):
        return str(self.name)

status = Status.__table__
table  = Status.__table__

status.primary_key.name='%s_pk'%(_TN)
status.append_constraint(UniqueConstraint('name',name='%s_uk'%(_TN)))


def populate(sess, *args, **kw):
    from sqlalchemy import insert
    from sqlalchemy.exceptions import IntegrityError

    if len(sess.query(Status).all()) < len(_statuses):
        i=status.insert()
        for name in _statuses:
            try:
                i.execute(name=name)
            except IntegrityError:
                pass

    assert len(sess.query(Status).all()) == len(_statuses)

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
