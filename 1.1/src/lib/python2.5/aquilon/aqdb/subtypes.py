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

import types
from datetime import datetime

#from db_factory      import db_factory
#from aqdbBase        import aqdbBase
#from schema          import (get_id_col, get_comment_col, get_date_col,
#                             get_date_default)

from db import (meta,engine, Session, Base, get_id_col, get_comment_col,
                get_date_col, get_date_default)

from sqlalchemy      import (Table, Column, Integer, String, DateTime, Index,
                             UniqueConstraint, PrimaryKeyConstraint, select)

from sqlalchemy.orm  import deferred

#subtype Base, make it have new __repr__, __str__, __eq__ methods.

# we want class level methods on the classes returned by subtype:
# LocationType.populate(), LocationType.id('foo')

#TODO: implement .id as a partial?
#def id(nm):
#    from sqlalchemy import select
#    engine = db_factory.get_engine()
#    sl=select([location_type.c.id], location_type.c.type=='%s'%(nm))
#    return engine.execute(sl).fetchone()[0]

def subtype(nm,tbl):
    """ A factory object for subtypes in Aqdb."""
    class klass(Base):
        """ The Discriminator for %s types"""%(nm)
        __tablename__ = 'location_type'
        id = Column(Integer,primary_key=True)
        type = Column(String(32), nullable = False)
        creation_date = deferred(Column(DateTime, nullable=False,
                                        default = get_date_default()))
        comments = deferred(Column(String(255)))

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
    klass.__table__.append_constraint(
        PrimaryKeyConstraint('id', name = '%s_pk'%(tbl)))
    klass.__table__.append_constraint(
        UniqueConstraint('type', name = '%s_uk'%(tbl)))
    klass.__name__ = nm
    return klass

def populate_subtype(cls, items):
    """ Shorthand for filling in types """
    if not cls.__table__:
        raise TypeError('class arg must have a __table__ attr')
    if isinstance(items,list):
        if len(items) > cls.__table__.count().execute().fetchone()[0]:
            #dbf = db_factory('sqlite')
            #s = dbf.session()
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

#SystemType
#Hardware/Machine Type
#Interface Type

#sys_types = ['base_system_type', 'host', 'afs_cell', 'host_list',
#             'quattor_server']


if __name__ == '__main__':
    pass

"""
Replaces:

class aqdbType(aqdbBase):
    ""To wrap rows in 'type' tables""
    @optional_comments
    def __init__(self,type,*args,**kw):
        if type.isspace() or len(type) < 1:
            msg='Names must contain some non-whitespace characters'
            raise ArgumentError(msg)
        if isinstance(type,str):
            self.type = type.strip().lower()
        else:
            raise ArgumentError("Incorrect name argument %s" %(type))
            return
    def name(self):
        return str(self.type)
    def __str__(self):
        return str(self.type)
    def __repr__(self):
        return self.__class__.__name__+" " +str(self.type)
"""
