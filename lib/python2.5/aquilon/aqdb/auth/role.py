#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Contains tables and objects for authorization in Aquilon """


import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from aquilon.aqdb.db_factory import Base
from aquilon.aqdb.table_types.name_table import make_name_class


Role = make_name_class('Role', 'role')
role = Role.__table__

def populate(*args, **kw):
    from aquilon.aqdb.db_factory import db_factory, Base
    from sqlalchemy import insert

    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    if 'debug' in args:
        Base.metadata.bind.echo = True
    s = dbf.session()

    role.create(checkfirst = True)

    if s.query(Role).count() == 0:
        roles=['nobody', 'operations', 'engineering', 'aqd_admin', 'telco_eng']
        for i in roles:
            r=Role(name = i, comments = 'AutoPopulated')
            s.save(r)
            assert(r)
        s.commit()
        print 'created %s'%(roles)

    if Base.metadata.bind.echo == True:
        Base.metadata.bind.echo == False
