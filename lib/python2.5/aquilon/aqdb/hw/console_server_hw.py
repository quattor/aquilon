#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" The hardware portion of a console_server """

from datetime import datetime
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy      import Table, Column, Integer, ForeignKey
from sqlalchemy.orm  import relation, deferred, backref

from aquilon.aqdb.hw.hardware_entity  import HardwareEntity

class ConsoleServerHw(HardwareEntity):
    __tablename__ = 'console_server_hw'
    __mapper_args__ = {'polymorphic_identity' : 'console_server_hw'}

    hardware_entity_id = Column(Integer,
                                ForeignKey('hardware_entity.id',
                                           name = 'cons_svr_hw_fk',
                                           ondelete = 'CASCADE'),
                                           primary_key = True)

    @property
    def hardware_name(self):
        if self.console_server:
            return ",".join(console_server.fqdn for console_server
                            in self.console_server)
        return self._hardware_name

console_server_hw = ConsoleServerHw.__table__
console_server_hw.primary_key.name = 'cons_svr_hw_pk'

table = console_server_hw

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
