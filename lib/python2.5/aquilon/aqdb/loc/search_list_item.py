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

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import (Column, Table, Integer, Sequence, String, DateTime,
                        ForeignKey, UniqueConstraint, Index)

from sqlalchemy.orm import relation, deferred, backref
from sqlalchemy.ext.orderinglist import ordering_list

from aquilon.aqdb.db_factory import Base
from aquilon.aqdb.column_types.aqstr import AqStr
from aquilon.aqdb.loc.location_search_list import LocationSearchList


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

    creation_date = deferred(Column(DateTime, default = datetime.now,
                                    nullable = False))
    comments      = deferred(Column(String(255), nullable = True))

    lsl = relation(LocationSearchList)
#TODO: add better str and repr methods:
#In [20]: sli1
#Out[20]: SearchListItem instance <--- should read 'chassis'



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
    from aquilon.aqdb.db_factory import db_factory, Base
    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    if 'debug' in args:
        Base.metadata.bind.echo = True
    s = dbf.session()

    search_list_item.create(checkfirst = True)

    m = s.query(LocationSearchList).first()
    assert m

    if len(s.query(SearchListItem).all()) < 1:

        sli1 = SearchListItem(location_type = 'chassis', lsl = m, position = 1)
        sli2 = SearchListItem(location_type = 'rack', lsl = m, position = 2)
        sli3 = SearchListItem(location_type = 'building', lsl = m, position = 3)
        sli4 = SearchListItem(location_type = 'city', lsl = m, position = 4)
        sli5 = SearchListItem(location_type = 'country', lsl = m, position = 5)
        sli6 = SearchListItem(location_type = 'continent', lsl = m, position = 6)
        sli7 = SearchListItem(location_type = 'hub', lsl = m, position = 7)
        sli8 = SearchListItem(location_type = 'world', lsl = m, position = 8)

        for i in (sli1, sli2, sli3, sli4, sli5, sli6, sli7):
            s.add(i)
            s.commit()

        print 'created Location Search List %s '%(m)

    cnt = len(s.query(SearchListItem).all())
    assert cnt > 6

    if Base.metadata.bind.echo == True:
        Base.metadata.bind.echo == False
