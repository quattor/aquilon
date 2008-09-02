#!/ms/dist/python/PROJ/core/2.5.0/bin/python
"""Class and Table relating to network interfaces"""

from datetime import datetime
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import (Column, Table, Integer, Sequence, Index, String,
                        Boolean, CheckConstraint, UniqueConstraint, DateTime,
                        ForeignKey)

from sqlalchemy.orm import relation, deferred

from aquilon.aqdb.db_factory         import Base
from aquilon.aqdb.column_types.aqstr import AqStr
from aquilon.aqdb.column_types.IPV4  import IPV4
from aquilon.aqdb.net.network        import Network
from aquilon.aqdb.hw.hardware_entity import HardwareEntity

class Interface(Base):
    __tablename__ = 'interface'

    id                = Column(Integer,
                            Sequence('interface_seq'), primary_key=True)

    name              = Column(AqStr(32), nullable = False)
    interface_type    = Column(AqStr(32), nullable = False) #TODO: index

    #interface_type_id = Column(Integer, ForeignKey(), nullable = False)

    hardware_entity_id     = Column(Integer, ForeignKey(HardwareEntity.c.id,
                                                    name = 'iface_hw_ent_fk',
                                                    ondelete = 'CASCADE'),
                                    nullable = False)

    bootable   = Column(Boolean, default = False)

    hardware_entity = relation(HardwareEntity, backref = 'interfaces',
                               passive_deletes = True)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable = False ))
    
    comments      = deferred(Column(String(255)))

    #network       = relation(Network, backref = 'interfaces' )
    #interface_type      = relation(InterfaceType)

    __mapper_args__ = {'polymorphic_on' : interface_type}

interface = Interface.__table__
interface.primary_key.name = 'interface_pk'

#Index('interface_net_id_idx', interface.c.network_id)

table = interface

#public are eth0, eth1. Must have a mac and must have a bootable flag
#standalone ipmi have a mac, bootable = False
#proxy impi share a public interface: have a duplicate mac, bootable = False
#ilo have a mac (proxied behind the chassis) OA
#ALL have an IP and a mac


# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-

