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

DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0,os.path.join(DIR, '..'))

from table_types.name_table import make_name_class

Archetype = make_name_class('Archetype','archetype')
archetype = Archetype.__table__
archetype.primary_key.name = 'archetype_pk'

def populate():
    from db_factory import db_factory, Base
    from debug import debug

    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    Base.metadata.bind.echo = True
    s = dbf.session()

    archetype.create(checkfirst=True)

    if len(s.query(Archetype).all()) < 1:
        a = Archetype(name='aquilon')
        s.add(a)
        s.commit()

        a = s.query(Archetype).first()
        assert(a)
