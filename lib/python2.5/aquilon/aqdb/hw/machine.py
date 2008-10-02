#!/ms/dist/python/PROJ/core/2.5.0/bin/python
"""The tables/objects/mappings related to hardware in Aquilon. """

from datetime import datetime
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy      import (UniqueConstraint, Table, Column, Integer,
                            DateTime, Sequence, String, select, ForeignKey,
                            Index)

from sqlalchemy.orm  import relation, deferred, backref

from aquilon.aqdb.column_types.aqstr  import AqStr
from aquilon.aqdb.hw.hardware_entity  import HardwareEntity
from aquilon.aqdb.hw.cpu              import Cpu
from aquilon.aqdb.cfg.cfg_path        import CfgPath

#TODO: use selection of the machine specs to dynamically populate default
#     values for all of the attrs where its possible

class Machine(HardwareEntity):
    __tablename__ = 'machine'
    __mapper_args__ = {'polymorphic_identity' : 'machine'}

    #hardware_entity_
    id = Column(Integer, ForeignKey('hardware_entity.id',
                                           name = 'machine_hw_ent_fk'),
                                           primary_key = True)

    name = Column('name', AqStr(64), nullable = False)

    cpu_id = Column(Integer, ForeignKey(
        'cpu.id', name = 'machine_cpu_fk'), nullable = False)

    cpu_quantity = Column(Integer, nullable = False, default = 2) #constrain/smallint

    memory = Column(Integer, nullable = False, default = 512)

    hardware_entity = relation(HardwareEntity, uselist = False,
                               backref = 'machine', passive_deletes = True)

    cpu      = relation(Cpu, uselist = False)

    #TODO: synonym in location/model?
    #location = relation(Location, uselist = False)

machine = Machine.__table__

machine.primary_key.name = 'machine_pk'

machine.append_constraint(
    UniqueConstraint('name',name = 'machine_name_uk')
)

table = machine

#TODO:
#   check if it exists in dbdb minfo, and get from there if it does
#   and/or -dsdb option, and, make machine --like [other machine] + overrides

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
