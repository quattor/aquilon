#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" Base class of polymorphic hardware structures """
from datetime import datetime
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy     import (Column, Table, Integer, Sequence, ForeignKey,
                            Index, String, DateTime)
from sqlalchemy.orm import relation, deferred

from aquilon.aqdb.db_factory              import Base
from aquilon.aqdb.column_types.aqstr      import AqStr
from aquilon.aqdb.loc.location            import Location
from aquilon.aqdb.hw.model                import Model

#valid types are machine, tor_switch, chassis, console_switch
class HardwareEntity(Base):
    __tablename__ = 'hardware_entity'

    id  = Column(Integer, Sequence('hardware_entity_seq'), primary_key=True)

    hardware_entity_type = Column(AqStr(64), nullable=False)

    location_id          = Column(Integer, ForeignKey('location.id',
                                            name='hw_ent_loc_fk'),
                                            nullable=False)

    model_id             = Column(Integer, ForeignKey('model.id',
                                            name='hw_ent_model_fk'),
                                            nullable=False)

    serial_no            = Column(String(64), nullable = True)

    creation_date = deferred(Column(DateTime, default = datetime.now,
                                                nullable = False ))
    comments      = deferred(Column(String(255), nullable = True))

    location = relation(Location, uselist = False)
    model    = relation(Model, uselist = False)

    __mapper_args__ = {'polymorphic_on' : hardware_entity_type}

    @property
    def hardware_name(self):
        return 'Unnamed hardware'

hardware_entity = HardwareEntity.__table__
hardware_entity.primary_key.name = 'hardware_entity_pk'
Index('hw_ent_loc_idx',  hardware_entity.c.location_id)

table = hardware_entity

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
