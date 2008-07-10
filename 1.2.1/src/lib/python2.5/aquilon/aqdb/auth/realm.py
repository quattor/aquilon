#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Enumerates kerberos realms """
import sys
import os

DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0,os.path.join(DIR, '..'))


from table_types.name_table import make_name_class

Realm = make_name_class('Realm', 'realm')
realm = Realm.__table__

def populate_realm():
    if s.query(Realm).count() == 0:
        r = Realm(name = 'is1.morgan')
        s.save(r)
        s.commit()
        assert(r)
        print 'created %s'%(r)
