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

from depends import *
from schema import get_id_col

class LocationSearchList(Base):
    __table__ = Table('location_search_list', Base.metadata,
        get_id_col('location_search_list'),
        Column('name', String(32), nullable = False),
        Column('comments', String(255), nullable=True),
        Column('creation_date', DateTime, default=datetime.now),
        UniqueConstraint('name', name = 'loc_srch_list_uk'))

location_search_list = LocationSearchList.__table__
