#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
from datetime import datetime
import sys
import os

DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0,os.path.join(DIR, '..'))

import depends
from sqlalchemy import (Column, Table, Integer, Sequence, String, DateTime,
                        ForeignKey, UniqueConstraint, Index)

from sqlalchemy.orm import relation, deferred, backref
from sqlalchemy.ext.orderinglist import ordering_list

from db_factory import Base
from column_types.aqstr import AqStr
from location_search_list import LocationSearchList

class SearchListItem(Base):
    """ Association object for location types to various lists for
        searching against service mapping. """

    __tablename__ = 'search_list_item'

    id = Column('id', Integer, Sequence('sli_seq'), primary_key = True)

    location_search_list_id = Column(Integer, ForeignKey(
        'location_search_list.id', ondelete = 'CASCADE',
        name = 'sli_list_fk'), nullable = False)

    location_type = Column(AqStr(32), nullable = False)

    position      = Column(Integer, nullable = False)

    creation_date = deferred(Column(DateTime, default = datetime.now))
    comments      = deferred(Column(String(255), nullable = True))

search_list_item = SearchListItem.__table__

search_list_item.primary_key.name = 'search_li_pk'

search_list_item.append_constraint(
    UniqueConstraint('id', 'location_type', name='sli_loc_typ_uk'))

search_list_item.append_constraint(
    UniqueConstraint('location_type', 'position',
                     name = 'sli_loc_typ_pos_uk'))

LocationSearchList.location_types = relation(SearchListItem,
                          collection_class = ordering_list('position'),
                            order_by = [SearchListItem.__table__.c.position])

def populate(*args, **kw):
    from db_factory import db_factory, Base
    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    if 'debug' in args:
        Base.metadata.bind.echo = True
    s = dbf.session()

    search_list_item.create(checkfirst = True)
