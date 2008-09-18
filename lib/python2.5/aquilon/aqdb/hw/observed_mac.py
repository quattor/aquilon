#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" Observed Mac's are represent the occurance of seeing a mac address on
    the cam table of a given switch. They are created to allow for automated
    machine builds and ip assignment """

from datetime import datetime
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import Table, Column, Integer, DateTime, Sequence, ForeignKey
from sqlalchemy.orm                  import relation, deferred, backref
from sqlalchemy.ext.associationproxy import association_proxy

from aquilon.aqdb.db_factory         import Base
from aquilon.aqdb.net.network        import Network
from aquilon.aqdb.sy.tor_switch      import TorSwitch
from aquilon.aqdb.column_types.aqmac import AqMac

class ObservedMac(Base):
    """ reports the observance of a mac address on a switch port. """
    __tablename__ = 'observed_mac'

    #TODO: code level constraint on machine_type == tor_switch
    switch_id    = Column(Integer, ForeignKey(TorSwitch.c.id,
                                              ondelete = 'CASCADE',
                                              name = 'obs_mac_hw_fk'),
                                             primary_key = True)

    port_number  = Column(Integer, primary_key=True)

    mac_address  = Column(AqMac(17), nullable=False, primary_key=True)

    slot          = Column(Integer, nullable=True, default=1, primary_key=True)

    creation_date = deferred(Column('creation_date', DateTime,
                            default = datetime.now, nullable = False))

    last_seen     = deferred(Column('last_seen', DateTime,
                            default = datetime.now, nullable = False))

    switch = relation(TorSwitch, uselist=False,
                      backref=backref('ObservedMac', cascade='delete'))

    #TODO: selectable relation to interface/machine/system?

observed_mac = ObservedMac.__table__
observed_mac.primary_key.name = 'observed_mac_pk'

table = observed_mac

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
