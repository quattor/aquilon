""" Top of Rack Switches """

from sqlalchemy import Integer, Column, ForeignKey
from sqlalchemy.orm import relation, backref

from aquilon.aqdb.model import System, TorSwitchHw

class TorSwitch(System):
    __tablename__ = 'tor_switch'

    id = Column(Integer,
                ForeignKey('system.id', ondelete='CASCADE',
                           name='tor_sw_sys_fk'), primary_key=True)

    tor_switch_id = Column(Integer, ForeignKey('tor_switch_hw.hardware_entity_id',
                                               name='tor_sw_sy_hw.fk',
                                               ondelete='CASCADE'),
                                              nullable=False)

    tor_switch_hw = relation(TorSwitchHw, uselist=False,
                             backref=backref('tor_switch',cascade='delete'))

    __mapper_args__ = {'polymorphic_identity' : 'tor_switch'}

tor_switch = TorSwitch.__table__
tor_switch.primary_key.name='tor_switch_pk'

table = tor_switch

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
