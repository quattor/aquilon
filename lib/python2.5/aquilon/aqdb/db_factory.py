#!/ms/dist/python/PROJ/core/2.5.0/bin/python
"""To be imported by classes and modules requiring aqdb access"""
from __future__ import with_statement

import pwd
import getpass
import sys
import os
import StringIO

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy                  import __version__ as SA_version
from sqlalchemy                  import MetaData, engine, create_engine, text
from sqlalchemy.orm              import scoped_session, sessionmaker
from sqlalchemy.exceptions       import SQLError, DatabaseError as SaDBError
from sqlalchemy.ext.declarative  import declarative_base

from aquilon.config import Config

if '--debug' in sys.argv:
    from aquilon.aqdb.utils.shutils import ipshell
else:
    ipshell = lambda: "No ipshell imported"

def debug(examinee,*args,**kw):
    if '--debug' in sys.argv:
        if isinstance(examinee,str) and not kw.has_key('assert_only'):
            sys.stderr.write('%s\n'%(examinee))
        else:
            if kw.has_key('assert_only'):
                assert(examinee)
            else:
                assert(examinee, 'Object is: %s'%(examinee))
    else:
        pass

def noisy_exit(msg=None):
    if not msg:
        #TODO: get the traceback another way
        msg = 'Unhandled Exception...'
    sys.stderr.write('%s\n'%msg)
    sys.exit(9)

def monkeypatch(cls):
    def decorator(func):
        setattr(cls, func.__name__, func)
        return func
    return decorator

Base = declarative_base()

@monkeypatch(Base)
def __repr__(self):
    if hasattr(self,'name'):
        return self.__class__.__name__ + ' ' + str(self.name)
    elif hasattr(self,'type'):
        return self.__class__.__name__ + ' ' + str(self.type)
    elif hasattr(self,'service'):
        return self.__class__.__name__ + ' ' + str(self.service.name)
    elif hasattr(self,'system'):
        return self.__class__.__name__ + ' ' + str(self.system.name)
    else:
       return '%s instance '%(self.__class__.__name__)

#mk_table: could take an engine, meta, full dbf or a file

@monkeypatch(Base)
def mk_table(*args, **kw):
    if hasattr(self,'__table__'):
        print 'would create a table'
        #self.__table__.create(checkfirst=True)
    else:
        raise TypeError('%s has no __table__ attribute'%(self.__class__))

class db_factory(object):
    __shared_state = {}

    def __init__(self,*args, **kw):
        #TODO: accept mock as arg
        self.__dict__ = self.__shared_state

        try:
            self.config = Config()
        except Exception, e:
            print >> sys.stderr, "failed to read configuration: %s" % e
            sys.exit(os.EX_CONFIG)

        self.dsn = self.config.get('database', 'dsn')

        #Handle Mock Engine
        if 'mock' in args:
            self.mock = True
            self.buf = StringIO.StringIO()
            self.outfile = kw.pop('outfile','/tmp/DDL.sql')
            self.engine = create_engine(self.dsn,
                                        strategy='mock',
                                        executor = self.buffer_output)
        #ORACLE
        elif self.dsn.startswith('oracle'):
            import cx_Oracle
            self.schema = self.config.get('database','dbuser')

            passwds = self._get_password_list()

            if len(passwds) < 1:
                passwds.append(
                    getpass.getpass(
                        'Can not determine your password (%s).\nPassword:'%(
                            self.dsn)))
            self.login(passwds)
            debug(self.engine, assert_only = True)

        #SQLITE
        elif self.dsn.startswith('sqlite'):
            self.engine = create_engine(self.dsn)
            self.connection = self.engine.connect()
        else:
            msg = """
supported database datasources are sqlite and oracle, your dsn is '%s' """%(
    self.dsn).lstrip()

            noisy_exit(msg)
        assert(self.dsn)
        assert(self.engine)

        self.meta   = MetaData(self.engine)
        assert(self.meta)

        if SA_version.startswith('0.4'):
            self.Session = scoped_session(sessionmaker(bind = self.engine,
                                                       autoflush = True,
                                                       transactional = True))
        else:
            self.Session = scoped_session(sessionmaker(bind=self.engine))
        assert(self.Session)

        self.s = self.Session()

    def session(self):
        return self.Session()

    def login(self,passwds):
        errs = []
        import re
        pswd_re = re.compile('PASSWORD')
        dsn_copy = self.dsn

        for p in passwds:
            self.dsn = re.sub(pswd_re,p,dsn_copy)
            debug('trying dsn %s'%(self.dsn))

            self.engine = create_engine(self.dsn)

            try:
                self.connection = self.engine.connect()
                return
            except SaDBError, e:
                errs.append(e)
                pass
        if len(errs) >= 1:
            raise errs.pop()
        else:
            #shouldn't get here
            msg = 'unknown issue connecting to %s'%(self.dsn)
            raise SaDBError(msg)

    def _get_password_list(self):
        """ searches through PTS protected directory structure for file,
            which is multiline list of *all* passwords in age order descending
            (i.e. newest on top). It will try them sequentially, finally
            giving up and throwing an exception """

        if self.config.has_option("database", "dbpassword"):
            #TODO: RAISE WARNING: we'd like to get out of that buisness I think
            return [self.config.get("database", "dbpassword")]
        else:
            passwd_file = self.config.get("database", "password_file")
            passwds = []

            try:
                f = open(passwd_file)
                passwds = f.readlines()
                if len(passwds) < 1:
                    msg = "No lines in %s"%(passwd_file)
                    raise ValueError(msg)
                else:
                    return [passwd.strip() for passwd in passwds]
            # Fallback for testing when password file may not exist.
            except IOError,e:
                print e
                return None

    def safe_execute(self, stmt, *args, **kw):
        """ convenience wrapper """
        #debug('in safe execute with args: %s, kw: %s'%(args, kw))

        dbg = kw.pop('debug', False)
        verbose = kw.pop('verbose', False)

        if debug == True:
            verbose = True

        if dbg or verbose:
            print '%s'%(stmt)

        if dbg == True:
            return True

        try:
            return self.engine.execute(text(stmt), **kw)
        except SQLError, e:
            print >> sys.stderr, e

    def get_id(self, table, key, value):
        """Convenience wrapper"""
        res = self.safe_execute("SELECT id from %s where %s = :value"
                % (table, key), value=value)
        if res:
            rows = res.fetchall()
            if rows:
                return rows[0][0]
        return

    def buffer_output(self, s, p=""):
        return self.buf.write(s + p)

    def flush_to_file(self, outfile=None, *args, **kw):
        if outfile:
            with open(outfile, 'w') as f:
                f.write(self.buf.getvalue())
        else:
            print >> sys.stderr, self.buf.getvalue()

if __name__ == '__main__':
    if '-d' in sys.argv:
        print 'use --debug instead of -d'
        sys.exit(1)

    #THE BORG OBJECT MAKES THIS IMPOSSIBLE TO TEST IN A SINGLE FILE...
    #leave the obvious stuff out since everything imports this. We'll know if
    #it's broken.

    #debug('Testing creation of factory...')
    #db = db_factory()
    #debug(db.engine)
    #debug(db.meta)
    #del(db)

    debug('\n\nTesting MockEngine')
    outfile='/tmp/mock.sql'

    db2 = db_factory('mock')
    db2.dsn = 'oracle://satest:satest@nyt-aqdb.one-nyp.ms.com:1521/AQUILON'

    from sqlalchemy import Table, Column, Integer, String
    t1 = Table('db_factory_test_table', db2.meta,
               Column('c1', Integer, primary_key = True),
               Column('c2', String(20)))

    db2.meta.create_all()
    db2.flush_to_file(outfile)

    debug(os.path.isfile(outfile))
    #os.system('/bin/cat %s'%(outfile))

    #TODO: assert the has the right content with cached copy?
    debug('removing %s'%(outfile))
    os.remove(outfile)

    debug('writing from buffer to stderr...')

    #can't use debug() here because it will *always write to stderr...
    if '--debug' in sys.argv:
        db2.flush_to_file()

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-

