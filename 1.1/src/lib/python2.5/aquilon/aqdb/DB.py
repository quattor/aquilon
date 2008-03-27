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
from sqlalchemy.orm import sessionmaker, scoped_session

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

sqlite_dsn = make_sqlite_dsn()
oracle_dsn='oracle://aqd:hello@aquilon'

"""
    CONFIGURES THE DSN FOR THE ENTIRE PROJECT
"""
dsn = sqlite_dsn

engine = create_engine(dsn)
engine.connect()
meta  = MetaData(engine)

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
