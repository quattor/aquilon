#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" copied for migration """
import sys
sys.path.insert(0,'..')

from depends import *
from host_list import host_list
from host import host

class HostListItem(Base):
    __table__ = Table('host_list_item', Base.metadata,

    Column('host_list_id', Integer,
           ForeignKey('host_list.id', ondelete='CASCADE', name='hli_hl_fk'),
           primary_key = True),
    Column('host_id', Integer,
           ForeignKey('host.id', ondelete='CASCADE', name='hli_host_fk'),
           nullable=False, primary_key=True),
    Column('position', Integer, nullable=False),
    Column('creation_date', DateTime, default=datetime.now),
    Column('comments', String(255), nullable=True),
    PrimaryKeyConstraint('host_list_id', 'host_id', name = 'host_list_item_pk'),
    UniqueConstraint('host_id', name='host_list_item_uk'))

host_list_item=HostListItem.__table__
