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


import types
from datetime import datetime
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import (Table, Column, Sequence, Integer, String, DateTime,
                        UniqueConstraint, PrimaryKeyConstraint, select)
from sqlalchemy.orm import deferred

from aquilon.aqdb.db_factory import Base


# we want class level methods on the classes returned by subtype:
# LocationType.populate(), LocationType.id('foo')

#TODO: implement .id as a partial?
#def id(nm):
#    from sqlalchemy import select
#    engine = db_factory.get_engine()
#    sl=select([location_type.c.id], location_type.c.type=='%s'%(nm))
#    return engine.execute(sl).fetchone()[0]

def subtype(nm,tbl,dstr=None):
    """ A factory object for subtypes in Aqdb."""
    class klass(Base):
        """ The Discriminator for %s types"""%(nm)

        __table__= Table(tbl, Base.metadata,
                Column('id', Integer,
                       Sequence('%s_seq'%tbl), primary_key=True),
                Column('type', String(32), nullable=False),
                Column('creation_date', DateTime,
                       default=datetime.now, nullable = False),
                Column('comments', String(255), nullable = True),
                PrimaryKeyConstraint('id', name = '%s_pk'%tbl),
                UniqueConstraint('type',name = '%s_uk'%tbl))

        def __str__(self):
            return str(self.type)

        def __repr__(self):
            return self.__class__.__name__ + " " + str(self.type)

        def __eq__(self,other):
            if isinstance(other,str):
                if self.type == other:
                    return True
                else:
                    return False
            else:
                raise ArgumentError('Can only be compared to strings')
    if dstr:
        klass.__doc__ = dstr
    klass.__name__ = nm
    return klass

def populate_subtype(cls, items):
    """ Shorthand for filling in types """
    if not cls.__table__:
        raise TypeError('class arg must have a __table__ attr')
    if isinstance(items,list):
        if len(items) > cls.__table__.count().execute().fetchone()[0]:
            s = Session()
            for t in items:
                test = s.query(cls).filter_by(type=t).all()
                if not test:
                    st = cls(type=t, comments='auto populated')
                    s.save(st)
                    s.commit()
    else:
        raise TypeError('items arg must be a list')

def get_subtype_id(nm=None,engine=None,cls=None):
    """ To keep session out of __init__ methods for systems """
    tbl = cls.__table__
    assert isinstance(tbl,Table)
    sl=select([tbl.c.id], tbl.c.type=='%s'%(nm))
    return engine.execute(sl).fetchone()[0]
