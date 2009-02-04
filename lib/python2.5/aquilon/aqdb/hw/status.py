""" Status is an overloaded term, but we use it to represent various stages of
    deployment, such as production, QA, dev, etc. each of which are also
    overloaded terms... """

from aquilon.utils import monkeypatch
from aquilon.aqdb.table_types.name_table import make_name_class

_statuses = ['blind', 'build', 'ready', 'failed']

Status = make_name_class('Status','status')
status = Status.__table__
table = status

@monkeypatch(Status)
def __init__(self,name):
    e = "Status is a static table and can't be instanced, only queried."
    raise ValueError(e)

@monkeypatch(Status)
def __repr__(self):
    return str(self.name)

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
