#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquiloni
""" The named parent table for lists of location types to search service
    maps later on when automatic configuration of services takes places """
import sys
import os

DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(DIR, '..'))
from db_factory import Base
from table_types.name_table import make_name_class

LocationSearchList = make_name_class('LocationSearchList',
                                     'location_search_list')

location_search_list = LocationSearchList.__table__
location_search_list.primary_key.name = 'loc_search_list_pk'

def populate(*args, **kw):
    from db_factory import db_factory, Base
    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    if 'debug' in args:
        Base.metadata.bind.echo = True
    s = dbf.session()

    location_search_list.create(checkfirst = True)
