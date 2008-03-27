#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""
    Utilities to decrease repeated code in generating schema
    and associated baseline data
"""

from sqlalchemy import *
from sqlalchemy import Column as _Column
import datetime

def optional_comments(func):
    def comments_decorator(*__args, **__kw):
        ATTR = 'comments'
        if (__kw.has_key(ATTR)):
            setattr(__args[0], ATTR, __kw.pop(ATTR))
        return func(*__args, **__kw)
    return comments_decorator

"""
    "decorate" column from SA to default as null=False
    unless it's comments, which we hardcode to standardize
"""

def Column(*args, **kw):
    if not kw.has_key('nullable'):
        kw['nullable']=False;
    return _Column(*args, **kw)


def fill_type_table(table,items):
    """
        Shorthand for filling up simple 'type' tables
    """
    if not isinstance(table,Table):
        raise TypeError("table argument must be type Table")
        return
    if not isinstance(items,list):
        raise TypeError("items argument must be type list")
        return
    i = insert(table)
    for t in items:
        result = i.execute(type=t)


"""
    Function mk_name_id_table:
        args: Table name
        returns: a table with an id and a unique, non null indexed name column

    Reduces code volume for the 'type' tables of other subtypes
    Even though there are typically a small # of subtypes, 2NF relational
    best practices dictate that we pull them out for several reasons.

    Major functional areas with subtypes are:
        -Top level namespace categories (hardware, services, os, features)
        -Location (continent, city. building)
        -System: hides host, afs cell, sybase instance, etc.
        -Configuration systems (quattor, aqdb, cola... in the future))
        -Network interfaces (physical, zebra, other)
"""
#COMMENTS???
def mk_name_id_table(name, meta, *args, **kw):
    """
        Many tables simply contain name and id columns, use this
        to reduce code volume and standardize DDL
    """
    return Table(name, meta, \
                Column('id', Integer, Sequence('%s_id_seq',name),
                       primary_key=True),
                Column('name', String(32), unique=True, index=True),
                Column('creation_date', DateTime,
                       default=datetime.datetime.now),
                Column('comments', String(255), nullable=True),*args,**kw)


#COMMENTS FOR TYPE???
def mk_type_table(name, meta, *args, **kw):
    """
        Variant on name_id. Can and should reduce them to a single function
        (later)
    """
    return Table(name, meta, \
                Column('id', Integer, Sequence('%s_id_seq',name),
                       primary_key=True),
                Column('type', String(32), unique=True, index=True),
                Column('creation_date', DateTime,
                       default=datetime.datetime.now),
                Column('comments', String(255), nullable=True))

def add_compulsory_columns(tab):
    """ Every table should have this column. Later we'll use this to add
        owner and entitlement columns. """
    tab.append_column(
        Column('creation_date', DateTime,
               default=datetime.datetime.now))
    tab.append_column(Column('comments', String(255), nullable=True))

def empty(table, engine):
    """
        Returns True if no rows in table, helps in interative schema population
    """
    count = engine.execute(table.count()).fetchone()[0]
    if count < 1:
        return True
    else:
        return False
