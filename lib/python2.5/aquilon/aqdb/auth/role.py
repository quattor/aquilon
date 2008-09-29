#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
""" Contains tables and objects for authorization in Aquilon """

import sys
import os

from aquilon.aqdb.table_types.name_table import make_name_class

Role = make_name_class('Role', 'role')
role = Role.__table__
table = role

def populate(db, *args, **kw):
    roles=['nobody', 'operations', 'engineering', 'aqd_admin', 'telco_eng']

    if db.s.query(Role).count() >= len(roles):
        return

    from sqlalchemy import insert

    #TODO: make like archetype, select it first

    for i in roles:
        r=Role(name = i, comments = 'AutoPopulated')
        db.s.add(r)
        assert(r)
    db.s.commit()
    print '\ncreated %s roles'%(len(roles))

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
