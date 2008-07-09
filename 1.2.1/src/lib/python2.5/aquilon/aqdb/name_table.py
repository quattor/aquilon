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

from db import (meta, engine, Base, Session, get_id_col, get_comment_col,
                get_date_col, get_date_default)


from sqlalchemy     import (Table, Column, Integer, String, DateTime, Sequence,
                            UniqueConstraint, PrimaryKeyConstraint, select)

from sqlalchemy.orm import deferred

from aquilon.exceptions_ import ArgumentError

def make_name_class(nm,tbl):
    """ A factory object for tables that consist only of a name attr """
    class klass(Base):
        """ The Object for %s rows"""%(nm)
        __table__= Table(tbl, Base.metadata,
                Column('id', Integer,
                       Sequence('%s_id_seq'%tbl), primary_key=True),
                Column('name', String(32), nullable=False),
                Column('creation_date', DateTime,
                       default=datetime.now, nullable = False),
                Column('comments', String(255), nullable = True),
                PrimaryKeyConstraint('id', name = '%s_pk'%tbl),
                UniqueConstraint('name', name = '%s_uk'%tbl))

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
