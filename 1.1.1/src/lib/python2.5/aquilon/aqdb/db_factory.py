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

import sys
import os
import pwd
import ConfigParser as cp

import msversion
msversion.addpkg('sqlalchemy','0.4.6','dist')
msversion.addpkg('cx-Oracle','4.3.3-10.2.0.1-py25','dist')

import cx_Oracle

from sqlalchemy import MetaData, engine, create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.exceptions import DatabaseError as SaDBError

from debug import debug, noisy_exit

_oracle_header = 'oracle://'

class Singleton(object):
    _instance = None
    def __new__(cls, *args, **kw):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__new__(cls, *args, **kw)
        return cls._instance

class db_factory(Singleton):
    def __init__(self, *args, **kw):
        try:
            self.dbtype = kw.pop('dbtype')
            self.env    = kw.pop('env')
        except KeyError:
            msg = 'keyword args must contain a dbtype and an env'
            noisy_exit(msg)

        debug(self.dbtype, assert_only = True)
        debug(self.env, assert_only = True)

        self.config = cp.SafeConfigParser()
        #TODO: un-hardcode this
        self.config.read('conf.cfg')

        if self.dbtype == 'oracle':
            try:
                self.dsn = self.config.get(self.env, 'dsn')
                #debug(self.dsn)

            except cp.NoOptionError:
                noisy_exit("Can't determine connect string:\n")
            except cp.NoSectionError:
                msg = ' '.join(["Invalid Environment supplied, check args",
                         "(you supplied '%s')\n"%self.env])
                noisy_exit(msg)

            passwds = self._get_password_list()

            self.login(passwds)
            debug(self.engine, assert_only = True)

        elif self.dbtype == 'sqlite':
            #TODO: move static strings to, and pull user from aquilon.config
            _sqlite_header = 'sqlite:///'
            _db_file_base  = '/var/tmp'
            user=pwd.getpwuid(os.getuid())[0]
            return _sqlite_header + os.path.join(
                _db_file_base,user,'aquilon.db')
        else:
            msg = 'dbtype can be either sqlite or oracle'
            noisy_exit(msg)
        assert(self.dsn)


        #if kw.has_key('mock'):
        #    self.sql_file =  kw['mock']
        #    self.engine = self.mock_engine()

        assert(self.engine)

        self.meta   = MetaData(self.engine)
        assert(self.meta)

    def meta(self):
        return self.meta

    def engine(self):
        return self.engine

    def session(self):
        return scoped_session(sessionmaker(bind=self.engine,
                                      autoflush=True,
                                      transactional=True))
    def login(self,passwds):
        errs = []
        import re
        pswd_re = re.compile('PASSWORD')
        dsn_copy = self.dsn

        for p in passwds:
            self.dsn = re.sub(pswd_re,p,dsn_copy)
            #debug(self.dsn)
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

        base = '/ms/dist/aquilon/PROJ/aqdbpasswd/incr' #TODO: from config
        passwd_file = os.path.join(base,self.env,
                                   self.config.get(self.env,'user'))

        passwds = []
        with open(passwd_file) as f:
            passwds = f.readlines()
        if len(passwds) < 1:
            msg = "No lines in %s"%(passwd_file)
            raise ValueError(msg)
        else:
            return [passwd.strip() for passwd in passwds]

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
    dbf = db_factory(dbtype='oracle',env='uat')
    debug(dbf.engine)
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
