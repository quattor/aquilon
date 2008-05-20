#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""If you can read this, you should be Documenting"""
import sys
sys.path.append('../..')

import types
from datetime import datetime

#from db_factory      import db_factory
#from aqdbBase        import aqdbBase
#from schema         import (get_id_col, get_comment_col, get_date_col,
#                             get_date_default)

from db import (meta, engine, Base, Session, get_id_col, get_comment_col,
                get_date_col, get_date_default)


from sqlalchemy     import (Table, Column, Integer, String, DateTime, Index,
                             UniqueConstraint, PrimaryKeyConstraint, select)

from sqlalchemy.orm import deferred

def get_name_table(nm,tbl):
    """ A factory object for tables that consist only of a name attr """
    class klass(Base):
        """ The Object for %s rows"""%(nm)
        __tablename__ = tbl
        id            = Column(Integer, primary_key = True)
        name          = Column(String(32), unique = True, nullable = False)
        creation_date = deferred(Column(DateTime, nullable = False,
                                        default = get_date_default()))
        comments = deferred(Column(String(255)))

        def __str__(self):
            return str(self.name)
        def __repr__(self):
            return self.__class__.__name__ + " " + str(self.name)

        def __eq__(self,other):
            if isinstance(other,str):
                if self.name == other:
                    return True
                else:
                    return False
            else:
                raise ArgumentError('Can only be compared to strings')

    klass.__table__.append_constraint(
        PrimaryKeyConstraint('id', name = '%s_pk'%(tbl)))
    klass.__table__.append_constraint(
        UniqueConstraint('name', name = '%s_uk'%(tbl)))
    klass.__name__ = nm
    return klass

def populate_name_table(cls, items):
    """ Shorthand for filling in name tables """
    if not cls.__table__:
        raise TypeError('class arg must have a __table__ attr')
    if isinstance(items,list):
        if len(items) > cls.__table__.count().execute().fetchone()[0]:
            #dbf = db_factory('sqlite')
            s = Session()
            for t in items:
                test = s.query(cls).filter_by(name=t).all()
                if not test:
                    st = cls(name=t, comments='auto populated')
                    s.save(st)
                    s.commit()
    else:
        raise TypeError('items arg must be a list')


#class HostList(Base):
#    """ The default system type used for ServiceInstances will be this
#        data structure, a list of hosts. """
#
#    __tablename__ = 'hostlist'
#    id   = Column(Integer, primary_key=True)
#    name = Column(String(64), nullable=False, unique=True)
#    creation_date = deferred(Column(DateTime, nullable=False,
#                                        default = get_date_default()))
#    comments = deferred(Column(String(255)))
