#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""To be imported by classes and modules requiring aqdb access"""

import msversion
msversion.addpkg('sqlalchemy','0.4.4','dist')
import datetime

from sqlalchemy import MetaData, create_engine,  UniqueConstraint
from sqlalchemy import Table, Integer, DateTime, Sequence, String
from sqlalchemy import Column as _Column
from sqlalchemy import ForeignKey as _fk
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.sql import insert

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

sqlite_dsn = make_sqlite_dsn()
oracle_dsn='oracle://aqd:aqd@LNTO_AQUILON_NY'

"""
    CONFIGURES THE DSN FOR THE ENTIRE PROJECT
"""
#dsn = sqlite_dsn
dsn = oracle_dsn

if dsn.startswith('oracle'):
    msversion.addpkg('cx-Oracle','4.3.3-10.2.0.1-py25','dist')
    import cx_Oracle
    import os
    import sys
    
    o_home = os.environ.get('ORACLE_HOME')
    if not o_home:
        print 'Oracle Home is not set, check the environment'
        sys.exit(1)
    o_sid = os.environ.get('ORACLE_SID')
    if not o_sid:
        print 'Oracle SID not found in environment, setting to test instance'
        os.environment['ORACLE_SID']='LNTO_AQUILON_NY'
    
engine = create_engine(dsn)
engine.connect()
meta  = MetaData(engine)

#if dsn.startswith('oracle'):
    #        meta.bind.echo = True


Session = scoped_session(sessionmaker(bind=engine,
                                      autoflush=True,
                                      transactional=True))

""" Some very important things about the selection of attributes in the
    sessionmaker call above:

    *   When using a transactional session, either a rollback() or a close() call
        is *required* when an error is raised by flush() or commit(). The
        flush() error condition will issue a ROLLBACK to the database
        automatically, but the state of the Session itself remains in an
        "undefined" state until the user decides whether to rollback or close.

    *   A commit() call unconditionally issues a flush(). Particularly when
        using transactional=True in conjunction with autoflush=True, explicit
        flush() calls are usually not needed.

    *   Session also supports Python 2.5's with statement so that we can:

        Session = sessionmaker(transactional=False)
        sess = Session()
        with sess.begin():
            item1 = sess.query(Item).get(1)
            item2 = sess.query(Item).get(2)
            item1.foo = 'bar'
            item2.bar = 'foo'

    Methods that can be called against objects pulled from session.query():

    *   expunge() removes an object from the Session, sending persistent
        instances-> detached state, and pending instances-> transient state.

    *   clear() expunges everything from the Session, but doesn't reset any
        transactional state or connection resources. What you usually want
        instead of clear is close()

    *   close() method issues a clear(), and releases any transactional or
        connection resources. When connections are returned to the connection
        pool, whatever transactional state exists is rolled back.

    *   reload()/expire(): to assist with the Session's "sticky" behavior,
        instances which are present, individual objects can have all of their
        attributes immediately reloaded from the database, or marked as
        "expired".
        This will cause a reload to occur upon the next access of any mapped
        attributes. This includes all relationships, so lazy-loaders will be
        re-initialized, eager relationships will be repopulated. Any changes
        marked on the object are discarded.

    Quickie review of Object States in the Session:

    *Transient: an instance that's not in a session, and is not
        saved to the database; i.e. it has no database identity. The only
        relationship such an object has to the ORM is that its class has a
        mapper() associated with it.

    *Pending: when you save() a transient instance, it becomes pending. It still
        wasn't actually flushed to the database yet, but it will be when the
        next flush occurs.

    *Persistent: An instance which is present in the session and has a record
        in the database. You get persistent instances by either flushing so
        that the pending instances become persistent, or by querying the
        database for existing instances (or moving persistent instances from
        other sessions into your local session).

    *Detached: an instance which has a record in the database, but is not in any
        session. Theres nothing wrong with this, and you can use objects
        normally when they're detached, except they will not be able to issue
        any SQL in order to load collections or attributes which are not yet
        loaded, or were marked as "expired".
"""

def optional_comments(func):
    """ reduce repeated code to handle 'comments' column """
    def comments_decorator(*__args, **__kw):
        ATTR = 'comments'
        if (__kw.has_key(ATTR)):
            setattr(__args[0], ATTR, __kw.pop(ATTR))
        return func(*__args, **__kw)
    return comments_decorator



class aqdbBase(object):
    """ AQDB base class: All ORM classes will extend aqdbBase. While the code
    is a bit trite, it would be silly not to have this class such that we can
    make use of it later when and if needed. All schema modules need to import
    db, so this is the best place for it
    """
    @optional_comments
    def __init__(self,name,*args,**kw):
        self.name = name
    def __repr__(self):
        if hasattr(self,'name'):
            return self.__class__.__name__ + " " + str(self.name)
        #elif hasattr(self,'canonical_name'):
        #    return self.__class__.__name__ + " " + str(self.canonical_name.name)
        elif hasattr(self,'system'):
            return self.__class__.__name__ + " " + str(self.system.name)
        else:
            return '%s instance '%(self.__class__.__name__)

class aqdbType(aqdbBase):
    """To wrap rows in 'type' tables"""
    @optional_comments
    def __init__(self,type,*args,**kw):
        self.type=type
    def name(self):
        return str(self.type)
    def __repr__(self):
        return str(self.type)

"""
    Utilities to decrease repeated code in generating schema
    and associated baseline data
"""

def Column(*args, **kw):
    """ some curry: default column from SA to default as null=False
        unless it's comments, which we hardcode to standardize
    """
    if not kw.has_key('nullable'):
        kw['nullable']=False;
    return _Column(*args, **kw)

def ForeignKey(*args, **kw):
    """ more curry: Oracle has 'on delete RESTRICT' by default
        This removes it in case you need to """

    if kw.has_key('ondelete'):
        if kw['ondelete'] == 'RESTRICT':
            kw.pop('ondelete')
    if kw.has_key('onupdate'):
        kw.pop('onupdate')
    return _fk(*args, **kw)


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
        sess.close()
    return cache

    """ Before we started using the thread local session, we needed to send
        the instance from the persistent state to the detached state with
        expire, so that when they are reused in another context they won't
        cause errors from being in the persistent state, and marked as
        "already attached to the session" which loaded them (because it was a
        different session). """

def empty(table, *args, **kw):
    """
        Returns True if no rows in table, helps in interative schema population
    """
    count = engine.execute(table.count()).fetchone()[0]
    if count < 1:
        return True
    else:
        return False

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


def mk_name_id_table(name, meta, *args, **kw):
    """
        Many tables simply contain name and id columns, use this
        to reduce code volume and standardize DDL
    """
    return Table(name, meta, \
                Column('id', Integer, Sequence('%s_id_seq'%name),
                       primary_key=True),
                Column('name', String(32), unique=True, index=True),
                Column('creation_date', DateTime,
                       default=datetime.datetime.now),
                Column('comments', String(255), nullable=True),*args,**kw)

def mk_type_table(name, meta, *args, **kw):
    """
        Variant on name_id. Can and should reduce them to a single function
        (later)
    """
    return Table(name, meta, \
                Column('id', Integer, Sequence('%s_id_seq'%name),
                       primary_key=True),
                Column('type', String(32), unique=True, index=True),
                Column('creation_date', DateTime,
                       default=datetime.datetime.now),
                Column('comments', String(255), nullable=True))
