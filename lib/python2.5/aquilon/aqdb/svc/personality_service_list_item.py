""" see class.__doc__ for description """

from datetime import datetime

from sqlalchemy import (Column, Table, Integer, Sequence, String, DateTime,
                        ForeignKey, UniqueConstraint, Index)
from sqlalchemy.orm import relation, backref

from aquilon.aqdb.base import Base
from aquilon.aqdb.sy   import Host
from aquilon.aqdb.cfg  import Personality
from aquilon.aqdb.svc  import Service

_TN  = 'personality_service_list_item'
_ABV = 'prsnlty_sli'

class PersonalityServiceListItem(Base):
    """ A personality service list item is an individual member of a list
       of required services for a given personality. They represent required
       services that need to be assigned/selected in order to build
       hosts in said personality """

    __tablename__ = _TN

    #id              = Column(Integer, Sequence('%s_seq'%(_ABV)),
    #                       primary_key=True)

    service_id      = Column(Integer, ForeignKey('service.id',
                                               name='%s_svc_fk'%(_ABV),
                                               ondelete='CASCADE'),
                           primary_key=True)

    personality_id  = Column(Integer, ForeignKey('personality.id',
                                                 name='sli_prsnlty_fk',
                                                 ondelete='CASCADE'),
                             primary_key=True)

    creation_date = Column(DateTime, default=datetime.now,
                                    nullable=False)
    comments      = Column(String(255), nullable=True)

    personality   = relation(Personality, backref='service_list')
    service       = relation(Service)

personality_service_list_item = PersonalityServiceListItem.__table__
table = personality_service_list_item

table.primary_key.name = '%s_pk'%(_ABV)

Index('%s_prsnlty_idx'%(_ABV), table.c.personality_id)


# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
