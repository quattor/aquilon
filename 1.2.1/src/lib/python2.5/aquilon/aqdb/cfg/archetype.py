#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Archetype specifies the metaclass of the build """


import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from aquilon.aqdb.table_types.name_table import make_name_class


Archetype = make_name_class('Archetype','archetype')
archetype = Archetype.__table__
archetype.primary_key.name = 'archetype_pk'

def populate(*args, **kw):
    from aquilon.aqdb.db_factory import db_factory, Base
    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    if 'debug' in args:
        Base.metadata.bind.echo = True
    s = dbf.session()

    archetype.create(checkfirst=True)

    if len(s.query(Archetype).all()) < 1:
        for a_name in ['aquilon', 'windows', 'aurora']:
            a = Archetype(name=a_name)
            s.add(a)
        s.commit()

        a = s.query(Archetype).first()
        assert(a)

    if Base.metadata.bind.echo == True:
        Base.metadata.bind.echo == False
