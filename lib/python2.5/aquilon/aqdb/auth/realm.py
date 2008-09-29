#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
""" Enumerates kerberos realms """

import sys
import os

from aquilon.aqdb.table_types.name_table import make_name_class


Realm = make_name_class('Realm', 'realm')
realm = Realm.__table__
table = realm

def populate(db, *args, **kw):
    if db.s.query(Realm).count() == 0:
        r = Realm(name = 'is1.morgan')
        db.s.add(r)
        db.s.commit()
        assert(r)
        #print 'created %s'%(r)

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
