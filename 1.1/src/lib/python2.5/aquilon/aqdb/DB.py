#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
'''To be imported by classes and modules requiring aqdb access'''

import msversion
msversion.addpkg('sqlalchemy','0.4.4','dist')

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker

#from sys import path
#path.append('./utils')
from aquilon.aqdb.utils.schemahelpers import optional_comments

def make_sqlite_dsn():
    import os
    import exceptions
    """Set up a default sqlite URI for use when none given."""
    osuser = os.environ.get('USER')
    dbdir = os.path.join( '/var/tmp', osuser, 'aquilondb' )
    try:
        os.makedirs( dbdir )
    except exceptions.OSError:
        pass
    return "sqlite:///" + os.path.join( dbdir, 'aquilon.db' )

#sqlite_file = '/tmp/aqdb/aquilon.db'
#sqlite_dsn = 'sqlite:///%s'%sqlite_file
sqlite_dsn = make_sqlite_dsn()
oracle_dsn='oracle://aqd:hello@aquilon'

"""
    CONFIGURES THE DSN FOR THE ENTIRE PROJECT
"""

dsn = sqlite_dsn
#dsn = oracle_dsn

engine = create_engine(dsn)
engine.connect()
meta  = MetaData(engine)

Session = sessionmaker(bind=engine)

""" The AQDB module base class.
    All ORM classes will extend aqdbBase. While this is currently empty,
    it would be silly not to have this class such that we can make use
    of it later when and if needed. Not sure it will exist here permanently
    but since all schema modules need to import DB, it's here for now
"""
class aqdbBase(object):
    @optional_comments
    def __init__(self,name,*args,**kw):
        self.name = name
    def __repr__(self):
        if hasattr(self,'name'):
            return self.__class__.__name__ + " " + str(self.name)
        elif hasattr(self,'canonical_name'):
            return self.__class__.__name__ + " " + str(self.canonical_name.name)
        elif hasattr(self,'system'):
            return self.__class__.__name__ + " " + str(self.system.name)
        else:
            return '%s instance '%(self.__class__.__name__)

class aqdbType(aqdbBase):
    """To wrap rows in 'type' tables"""
    @optional_comments
    def __init__(self,type,*args,**kw):
        self.type=type
    #def name(self):
    #    return str(self.type)
    def __repr__(self):
        return str(self.type)


""" Example of a 'mock' engine to output sql as print statments

    buf = StringIO.StringIO()
    def foo(s, p=None):
        print s
    engine=create_engine('sqlite:///:memory:',strategy='mock',executor=foo)
"""

def gen_id_cache(obj_name):
    """ A helper function for bulk creation. When you need to iterate over a
        result set creating either Location objects, or other tables like
        Network or Hardware which have FK's to a location id, this speeds things
        up quite a bit.

        Argument: the object name which wraps the table you're interested in
        Returns: a dictionary who's keys are the object's name, and values
        are the primary key (id) to the table they are in.
    """
    sess=Session()
    cache={}

    for c in sess.query(obj_name).all():
        cache[str(c.name)]=c
    return cache
