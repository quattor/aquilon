#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
import sys
sys.path.insert(0,'..')

from depends import *

class SearchListItem(Base):
    """ Association object for location types to various lists for
        searching against service mapping. """

    __table__ = Table('search_list_item', Base.metadata,
    Column('id', Integer, Sequence('sli_seq'), primary_key=True),
    Column('location_search_list_id', Integer,
        ForeignKey('location_search_list.id', ondelete='CASCADE',
            name='sli_list_fk'), nullable=False),
    Column('location_type_id', Integer,
           ForeignKey('location_type.id', ondelete='CASCADE',
               name='sli_loc_typ__fk'), nullable=False),
    Column('position', Integer, nullable=False),
    Column('creation_date', DateTime, default=datetime.now),
    Column('comments', String(255), nullable=True),
    UniqueConstraint('id','location_type_id',name='sli_loc_typ_uk'),
    UniqueConstraint('location_type_id','position',name='sli_loc_typ_pos_uk'))
