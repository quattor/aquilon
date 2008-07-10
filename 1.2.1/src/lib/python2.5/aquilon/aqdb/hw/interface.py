#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Classes and Tables relating to network interfaces"""
from datetime import datetime
import sys
import os

DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(DIR, '..'))

import depends

from sqlalchemy import (Column, Table, Integer, Sequence, String, Index,
                        DateTime)
from sqlalchemy.orm import mapper, relation, deferred

from column_types.aqstr  import AqStr
from db_factory          import Base

class Interface(Base):
    __tablename__ = 'interface'

    id = Column(Integer, Sequence('interface_id_seq'), primary_key=True)
    interface_type = Column(AqStr(16), nullable=False) #TODO: index
    ip = Column('ip', String(16), default='0.0.0.0', index=True)

    creation_date = deferred(Column('creation_date',
                                    DateTime, default=datetime.now))
    comments = deferred(Column('comments',String(255))) #TODO FK to IP table)

    __mapper_args__ = {'polymorphic_on' : interface_type}

interface = Interface.__table__
interface.primary_key.name = 'interface_pk'

def populate():
    from db_factory import db_factory, Base
    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    Base.metadata.bind.echo = True
    s = dbf.session()

    interface.create(checkfirst=True)
