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

DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(DIR, '..'))
from db_factory import Base
from table_types.name_table import make_name_class

Role = make_name_class('Role', 'role')
role = Role.__table__

def populate():
    from db_factory import db_factory, Base
    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    Base.metadata.bind.echo = True
    s = dbf.session()

    role.create(checkfirst = True)

    if s.query(Role).count() == 0:
        roles=['nobody', 'operations', 'engineering', 'aqd_admin']
        for i in roles:
            r=Role(name = i, comments = 'AutoPopulated')
            s.save(r)
            assert(r)
        s.commit()
        print 'created %s'%(roles)
