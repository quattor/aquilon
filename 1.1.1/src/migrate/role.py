#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Role for authorization, copied from auth.py for migration"""
from depends import *

class Role(Base):
    __table__ = Table('role', Base.metadata,
        Column('id', Integer, Sequence('role_id_seq'),
               primary_key=True),
        Column('name', String(32), nullable=False),
        Column('creation_date', DateTime,
               default = datetime.now, nullable = False),
        Column('comments', String(255), nullable=True),
        PrimaryKeyConstraint('id', name='role_pk'),
        UniqueConstraint('name', name='role_name_uk'))

role = Role.__table__
