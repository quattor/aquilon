#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Roles is a first cut at simple entitlements for the project """
import sys

from db import *

from sqlalchemy.orm import (mapper, relation, deferred)

class Role(Base):
    __table__ = Table('role', Base.metadata,
        Column('id', Integer, Sequence('roles_id_seq'),
               primary_key=True),
        Column('name', String(32), nullable=False),
        UniqueConstraint('name', name='role_name_uk'))
    comments = deferred(Column('comments',String(255),nullable=True))
    creation_date = deferred(
        Column('creation_date', DateTime, default=datetime.datetime.now))

    def __repr__(self):
        return self.__class__.__name__ + " " + str(self.name)

class Realm(Base):
    __table__ = Table('realm', meta,
    Column('id', Integer, Sequence('realm_id_seq'), primary_key=True),
    Column('name', String(64), nullable=False),
    UniqueConstraint('name',name='realm_uk'))

    comments = deferred(Column('comments',String(255),nullable=True))
    creation_date = deferred(
        Column('creation_date', DateTime, default=datetime.datetime.now))

    def __repr__(self):
        return self.__class__.__name__ + " " + str(self.name)

Base.metadata.create_all(engine)

if __name__ == '__main__':
    #Base.metadata.create_all(engine)
    s = Session()

    if s.query(Role).count() == 0:
        roles=['nobody','operations','engineering', 'aqd_admin']
        for i in roles:
            r=Role(name=i,comments='TEST')
            s.save(r)
            assert(r)
        s.commit()
        print 'created %s'%(roles)

    if s.query(Realm).count() == 0:
        r=Realm(name='is1.morgan')
        s.save(r)
        s.commit()
        assert(r)
        print 'created %s'%(r)
