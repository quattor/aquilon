""" The named parent table for lists of location types to search service
    maps later on when automatic configuration of services takes places """

from aquilon.aqdb.base import Base
from aquilon.aqdb.table_types.name_table import make_name_class

LocationSearchList = make_name_class('LocationSearchList',
                                     'location_search_list')

location_search_list = LocationSearchList.__table__
location_search_list.primary_key.name = 'loc_search_list_pk'

table = location_search_list

def populate(sess, *args, **kw):

    if len(sess.query(LocationSearchList).all()) < 1:
        l = LocationSearchList(name = 'full', comments = 'Chassis -> Company')
        sess.add(l)
        sess.commit()

    m = sess.query(LocationSearchList).first()
    assert m


# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
