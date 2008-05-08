#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" The types module incorporates all the various discriminator classes
    used by the project. Since they all must be pre-seeded to make the
    other modules load properly, we seperate them here to get them done
    before ahead of the other modules. """
import sys
sys.path.append('../..')

from db import *

from sqlalchemy.orm import (mapper, relation, deferred, backref)

class LocationType(Base):
    """ The discriminator for Location subtypes """
    __table__ = Table('location_type', Base.metadata,
        get_id_col('location_type'),
        Column('type', String(32), nullable = False),
        UniqueConstraint('type', name='location_type_uk'))

    creation_date = get_date_col()
    comments      = get_comment_col()
    def __str__(self):
        return str(self.type)

location_type = LocationType.__table__

def get_loc_type_id(typ_nm):
    """ To keep session out of __init__ methods for systems """
    sl=select([location_type.c.id], location_type.c.type=='%s'%(typ_nm))
    return engine.execute(sl).fetchone()[0]


class SystemType(Base):
    """ The discriminator for System """
    __table__ = Table('system_type', meta,
        get_id_col('system_type'),
        Column('type', String(32), nullable = False),
        UniqueConstraint('type', name='system_type_uk'))

    creation_date = get_date_col()
    comments      = get_comment_col()
    def __str__(self):
        return str(self.type)

system_type = SystemType.__table__

def get_sys_type_id(typ_nm):
        """ To keep session out of __init__ methods for systems """
        sl=select([system_type.c.id], system_type.c.type=='%s'%(typ_nm))
        return engine.execute(sl).fetchone()[0]

def populate_location_types():
    if empty(location_type):
        fill_type_table(location_type,['company','hub','continent','country',
                                   'city','bucket', 'building','rack','chassis',
                                   'desk', 'base_location_type'])

def populate_system_types():
    s = Session()
    types = ['base_system_type', 'host', 'afs_cell', 'host_list',
             'quattor_server']

    for t in types:
        test = s.query(SystemType).filter_by(type=t).all()
        if not test:
            st = SystemType(type=t, comments='auto populated')
            s.save(st)
            s.commit()

if __name__ == '__main__':

    Base.metadata.create_all(checkfirst=True)
    populate_location_types()
    populate_system_types()
