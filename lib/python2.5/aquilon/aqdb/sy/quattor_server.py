#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" At the moment, quattor servers are exposed as a very dull
    sublass of System """

import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import (Integer, String, Column, ForeignKey)
from sqlalchemy.orm import relation

from aquilon.aqdb.sy.system import System


class QuattorServer(System):
    __tablename__ = 'quattor_server'

    id = Column(Integer,
                ForeignKey('system.id', ondelete = 'CASCADE',
                           name = 'qs_system_fk'), primary_key = True)

    system = relation(System, uselist = False, backref = 'quattor_server')
    __mapper_args__ = {'polymorphic_identity' : 'quattor_server'}

quattor_server = QuattorServer.__table__
quattor_server.primary_key.name = 'qs_pk'

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
