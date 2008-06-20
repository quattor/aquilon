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
import datetime
import sys
sys.path.insert(0,'..')
sys.path.insert(1,'../..')
sys.path.insert(2,'../../..')

from db import Base
from name_table import make_name_class

Role = make_name_class('Role', 'role')
role = Role.__table__

def populate_role():
    if s.query(Role).count() == 0:
        roles=['nobody','operations','engineering', 'aqd_admin']
        for i in roles:
            r=Role(name=i,comments='TEST')
            s.save(r)
            assert(r)
        s.commit()
        print 'created %s'%(roles)
