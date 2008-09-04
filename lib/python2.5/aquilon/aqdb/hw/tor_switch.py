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
from aquilon.aqdb.hw.hardware_entity  import HardwareEntity

#TODO: use selection of the tor_switch specs to dynamically populate default
#     values for all of the attrs where its possible

class TorSwitch(HardwareEntity):
    __tablename__ = 'tor_switch'
    __mapper_args__ = {'polymorphic_identity' : 'tor_switch'}

    hardware_entity_id = Column(Integer,
                                ForeignKey(HardwareEntity.c.id,
                                           name = 'tor_switch_hw_ent_fk',
                                           ondelete = 'CASCADE'),
                                           primary_key = True)
    
    #TODO: Maybe still in flux, but hardware_entity's a_name should be
    # good enough.
    #name = Column('name', AqStr(64), nullable = False)

    hardware_entity = relation(HardwareEntity, uselist = False,
                               backref = 'tor_switch', passive_deletes = True)


tor_switch = TorSwitch.__table__
tor_switch.primary_key.name = 'tor_switch_pk'

#tor_switch.append_constraint(
#    UniqueConstraint('name',name = 'tor_switch_name_uk')
#)

table = tor_switch

#TODO: make tor_switch --like [other tor_switch] + overrides

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-

