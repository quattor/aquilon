""" Connection from any hardware entity to a serial_cnxn """

from datetime import datetime

from sqlalchemy      import (Table, Column, Integer, ForeignKey, Sequence,
                             UniqueConstraint)

from sqlalchemy.orm  import relation, deferred, backref

from aquilon.aqdb.db_factory         import Base
from aquilon.aqdb.column_types.aqstr import AqStr
from aquilon.aqdb.hw.hardware_entity import HardwareEntity
from aquilon.aqdb.sy.console_server  import ConsoleServer

class SerialCnxn(Base):
    """ serial connection: harware_ent/name/cons_svr/port# table. """

    __tablename__ = 'serial_cnxn'

    id = Column(Integer, Sequence(name='serial_cnxn_seq'), primary_key = True)

    console_server_id = Column(Integer,
                               ForeignKey('console_server.id',
                                           name='serial_cnxn_cons_svr_fk',
                                           ondelete='CASCADE'),
                               nullable = False)

    port_number = Column(Integer, nullable=False )

    hardware_entity_id = Column(Integer, ForeignKey('hardware_entity.id',
                                           name='serial_cnxn_hw_ent_fk',
                                           ondelete='CASCADE'),
                                nullable=False)

    name = Column(AqStr(64), nullable = False)

serial_cnxn = SerialCnxn.__table__
serial_cnxn.primary_key.name = 'serial_cnxn_pk'

serial_cnxn.append_constraint(UniqueConstraint(
    'console_server_id','port_number', name = 'serial_cnxn_cons_port_uk'))

serial_cnxn.append_constraint(UniqueConstraint(
    'hardware_entity_id', 'name', name = 'serial_cnxn_hw_name_uk'))

table = SerialCnxn.__table__

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
