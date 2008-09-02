#!/ms/dist/python/PROJ/core/2.5.0/bin/python
"""Class and Table relating to mac addresses"""

from datetime import datetime
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import (Column, Table, Integer, DateTime, ForeignKey)
from sqlalchemy.orm import relation, deferred

from aquilon.aqdb.db_factory         import Base
from aquilon.aqdb.column_types.aqmac import AqMac
from aquilon.aqdb.hw.interface       import Interface

class MacAddress(Base):
    """ mac address to interface association table: now as many to one """

    __tablename__ = 'mac_address'

    mac             = Column(AqMac(17), primary_key=True)

    interface_id        = Column(Integer, ForeignKey(Interface.c.id,
                                                 name = 'iface_mac_fk'))
    #NOTE: NULLABLE! this may not be the "right" way to do this

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable = False ))
    #this doesn't really garner comments
    #comments      = deferred(Column(String(255)))

    interface  = relation(Interface, backref = 'mac_addresses', passive_deletes = True)

mac_address = MacAddress.__table__
mac_address.primary_key.name = 'mac_addr_pk'

table = mac_address

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
