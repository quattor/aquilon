#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon

""" To fix up the network table's ddl during the migrate """
import sys
sys.path.insert(0,'..')

from depends import *

network = Table('network', Base.metadata,
    Column('id', Integer, Sequence('network_id_seq'), primary_key=True),
    Column('location_id', Integer,
        ForeignKey('location.id'), nullable=False),
    Column('network_type_id', Integer,
           ForeignKey('network_type.id'), nullable=False),
    Column('mask', Integer,
           ForeignKey('netmask.mask'), nullable=False),
    Column('name', String(255), nullable=False),
    Column('ip', String(15), nullable=False),
    Column('ip_integer', Integer, nullable=False),
    Column('byte_mask', Integer, nullable=False),
    Column('side', String(4), nullable=True),
    Column('dsdb_id', Integer, nullable=False),
    Column('creation_date', DateTime, default=datetime.now),
    Column('comments', String(255), nullable=True),
    PrimaryKeyConstraint('id', name = 'network_pk'),
    UniqueConstraint('dsdb_id',name='network_dsdb_id_uk'),
    UniqueConstraint('ip', name='net_ip_uk'))

Index('net_loc_id_idx', network.c.location_id)
