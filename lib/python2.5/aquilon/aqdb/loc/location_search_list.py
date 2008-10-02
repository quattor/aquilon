#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" The named parent table for lists of location types to search service
    maps later on when automatic configuration of services takes places """


import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends


from aquilon.aqdb.db_factory import Base
from aquilon.aqdb.table_types.name_table import make_name_class


LocationSearchList = make_name_class('LocationSearchList',
                                     'location_search_list')

location_search_list = LocationSearchList.__table__
location_search_list.primary_key.name = 'loc_search_list_pk'

table = location_search_list

def populate(db, *args, **kw):
    s = db.session()

    if len(s.query(LocationSearchList).all()) < 1:
        l = LocationSearchList(name = 'full', comments = 'Chassis -> Company')
        s.add(l)
        s.commit()

    m = s.query(LocationSearchList).first()
    assert m



#def fill():


# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
