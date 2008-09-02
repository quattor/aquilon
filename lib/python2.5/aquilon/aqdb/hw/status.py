#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" Status is an overloaded term, but we use it to represent various stages of
    deployment, such as production, QA, dev, etc. each of which are also
    overloaded terms... """

import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from aquilon.aqdb.db_factory import monkeypatch
from aquilon.aqdb.table_types.name_table import make_name_class

_statuses = ['production','development','qa','build']

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

def populate(db, *args, **kw):

    from sqlalchemy import insert

    s = db.session()

    status.create(checkfirst = True)

    if len(s.query(Status).all()) < 4:
        i=status.insert()
        for name in _statuses:
            i.execute(name=name)
        #can't do the usual since we made __init__ raise an Exception
        #    j = Status(name = i)
        #    s.add(j)
        #s.commit()

        i = s.query(Status).all()
        print 'created %s Statuses'%(len(i))

    assert len(s.query(Status).all()) == len(_statuses)




# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-

