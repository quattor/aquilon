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


from __future__ import with_statement

import pwd
import getpass
import sys
import os
import ConfigParser as cp

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..')))
    import aquilon.aqdb.depends

import sqlalchemy  #for version
from   sqlalchemy import MetaData, engine, create_engine, text
from   sqlalchemy.orm import scoped_session, sessionmaker
from   sqlalchemy.ext.declarative import declarative_base
from   sqlalchemy.exceptions import DatabaseError as SaDBError
from   sqlalchemy.exceptions import SQLError

from aquilon.config import Config
if '--debug' in sys.argv:
    from aquilon.aqdb.utils.shell import ipshell
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

class db_factory(object):
    __shared_state = {}
    def __init__(self, *args, **kw):
        #TODO: accept mock as arg
        self.__dict__ = self.__shared_state
        if hasattr(self,'config'):
            return

        try:
            self.config = Config()
        except Exception, e:
            print >> sys.stderr, "failed to read configuration: %s" % e
            sys.exit(os.EX_CONFIG)

        self.dsn = self.config.get('database', 'dsn')

        if self.dsn.startswith('oracle'):
            import cx_Oracle
            #Try with rfc-1738 style URI
            try:
                self.dsn = self.config.get('database', 'rfc-1738-dsn')
            except cp.NoOptionError, e:
                pass

            try:
                self.engine = create_engine(self.dsn)
                self.engine.connect()
            except SaDBError, e:
                print >> sys.stderr, e
                sys.exit(2)

            #look for the old style user/server combination
            if not self.engine:
                try:
                    self.schema = self.config.get('database','dbuser')
                    self.server = self.config.get('database','server')
                except cp.NoOptionError, e:
                    print e

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
            self.engine.connect()
        else:
            msg = """
supported database datasources are sqlite and oracle, your dsn is '%s' """%(
    self.dsn).lstrip()

            noisy_exit(msg)
        assert(self.dsn)
        assert(self.engine)

        self.meta   = MetaData(self.engine)
        assert(self.meta)
        print self.meta

        if sqlalchemy.__version__.startswith('0.4'):
            self.Session = scoped_session(sessionmaker(bind = self.engine,
                                                       autoflush = True,
                                                       transactional = True))
        else:
            self.Session = scoped_session(sessionmaker(bind=self.engine))
        assert(self.Session)

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
                self.engine.connect()
                return
            except SaDBError, e:
                errs.append(e)
                pass
        if len(errs) > 1:
            for e in errs:
                sys.stderr.write(e)
            raise SaDBError(errs[len(errs) - 1])
        elif len(errs) == 1:
            raise SaDBError(errs.pop())
        else:
            #shouldn't get here
            msg = 'unknown issue connecting to %s'%(self.dsn)
            raise SaDBError(msg)

    def _get_password_list(self):
        """ searches through PTS protected directory structure for file,
            which is multiline list of *all* passwords in age order descending
            (i.e. newest on top). It will try them sequentially, finally
            giving up and throwing an exception """

        passwd_file = self.config.get("database", "password_file")
        passwds = []
        if os.path.isfile(passwd_file):
           with open(passwd_file) as f:
                passwds = f.readlines()
                if len(passwds) < 1:
                    msg = "No lines in %s"%(passwd_file)
                    raise ValueError(msg)
                else:
                    return [passwd.strip() for passwd in passwds]
                        # Fallback for testing when password file may not exist.
        elif self.config.has_option("database", "dbpassword"):
            return [self.config.get("database", "dbpassword")]
        else:
            return []

    def safe_execute(self, stmt, **kwargs):
        """ convenience wrapper """
        try:
            return self.engine.execute(text(stmt), **kwargs)
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


class MockEngine(object):
    def __init__(self,*args, **kw):
        """ to write ddl statements to a file or stderr"""
        import StringIO
        #TODO: get default file from aquilon.config and integrate
        self.output_file = kw.pop('file',None)
        #TODO: unhardcode this and decide on encapsulation
        #      *is this the right place for an inner class?    #
        self.dsn = kw.pop('dsn','oracle://aqd:aqd@LNPO_AQUILON_NY')
        self.buffer = StringIO.StringIO()
        def executor(sql, *a, **kw):
            self.buffer.write(sql)
        self.engine = create_engine(self.dsn,strategy='mock', executor=executor)
        assert not hasattr(engine, 'mock')
        self.engine.mock = self.buffer

    def flush_to_file(self):
        if self.output_file:
            with open(self.output_file, 'w') as f:
                f.write(self.buffer.getvalue())
        else:
            print >> sys.stderr, self.buffer.getvalue()

if __name__ == '__main__':

    debug('Testing creation of factory...')
    dbf = db_factory()
    debug(dbf.engine)
    print dbf.engine
    debug(dbf.meta)
    debug(str(dbf.__dict__))
    del(dbf)
    debug('\n\n\n\nTesting MockEngine')

    mock_eng = MockEngine(dsn='sqlite://',file='/tmp/mock.sql')
    mock_eng2 = MockEngine(dsn='sqlite://')

    m1 = MetaData(mock_eng.engine)
    m2 = MetaData(mock_eng2.engine)

    from sqlalchemy import Table, Column, Integer, String
    for meta in [m1,m2]:
        t1 = Table('db_factory_test_table', meta,
               Column('c1', Integer, primary_key = True),
               Column('c2', String(20)))
        meta.create_all()
        debug(str(meta.tables))

    debug('writing to %s'%(mock_eng.output_file))
    mock_eng.flush_to_file()
    debug(os.path.isfile(mock_eng.output_file))
    #TODO: assert the has the right content with cached copy?
    debug('removing %s'%(mock_eng.output_file))
    os.remove(mock_eng.output_file)

    debug('writing from buffer to stderr...')
    #can't use debug() here because it will *always write to stderr...
    if '-d' in sys.argv:
        mock_eng2.flush_to_file()

    #ipshell()
