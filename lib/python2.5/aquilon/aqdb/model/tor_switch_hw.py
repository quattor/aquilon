""" Top of Rack Swtiches """
from datetime import datetime

from sqlalchemy      import Table, Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm  import relation, deferred, backref

from aquilon.aqdb.model import HardwareEntity

#TODO: use selection of the tor_switch_hw specs to dynamically populate
#      default values for all of the attrs where its possible

class TorSwitchHw(HardwareEntity):
    __tablename__ = 'tor_switch_hw'
    __mapper_args__ = {'polymorphic_identity' : 'tor_switch_hw'}

    #TODO: rename to id?
    hardware_entity_id = Column(Integer,
                                ForeignKey('hardware_entity.id',
                                           name = 'tor_switch_hw_ent_fk',
                                           ondelete = 'CASCADE'),
                                           primary_key = True)

    last_poll = Column(DateTime, nullable=False, default=datetime.now)

    @property
    def hardware_name(self):
        if self.tor_switch:
            return ",".join(tor_switch.fqdn for tor_switch in self.tor_switch)
        return self._hardware_name

tor_switch_hw = TorSwitchHw.__table__
tor_switch_hw.primary_key.name = 'tor_switch_hw_pk'

table = tor_switch_hw

#TODO: make tor_switch_hw --like [other tor_switch_hw] + overrides

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
