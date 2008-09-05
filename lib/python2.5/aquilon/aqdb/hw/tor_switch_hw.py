#!/ms/dist/python/PROJ/core/2.5.0/bin/python
"""The tables/objects/mappings related to hardware in Aquilon. """

from datetime import datetime
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import (UniqueConstraint, Table, Column, Integer, DateTime,
                        Sequence, String, select, ForeignKey, Index)

from sqlalchemy.orm  import relation, deferred, backref

from aquilon.aqdb.db_factory          import Base
from aquilon.aqdb.column_types.aqstr  import AqStr

#TODO: figure out how to do this with properties
#from aquilon.aqdb.net.network         import Network

from aquilon.aqdb.hw.hardware_entity  import HardwareEntity

#TODO: use selection of the tor_switch_hw specs to dynamically populate default
#     values for all of the attrs where its possible

class TorSwitch(HardwareEntity):
    __tablename__ = 'tor_switch_hw'
    __mapper_args__ = {'polymorphic_identity' : 'tor_switch_hw'}

    hardware_entity_id = Column(Integer,
                                ForeignKey(HardwareEntity.c.id,
                                           name = 'tor_switch_hw_ent_fk',
                                           ondelete = 'CASCADE'),
                                           primary_key = True)
    
    hardware_entity = relation(HardwareEntity, uselist = False,
                               backref = 'tor_switch_hw', passive_deletes = True)


tor_switch_hw = TorSwitch.__table__
tor_switch_hw.primary_key.name = 'tor_switch_hw_pk'

table = tor_switch_hw

#TODO: make tor_switch_hw --like [other tor_switch_hw] + overrides

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-

