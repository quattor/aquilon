"""To be imported by classes and modules requiring aqdb access"""
from __future__ import with_statement

import re
import os
import pwd
import sys

from getpass import getpass
from StringIO import StringIO

_DIR = os.path.dirname(os.path.realpath(__file__))
_LIBDIR = os.path.join(_DIR, '..', '..')

if _LIBDIR not in sys.path:
    sys.path.insert(0, _LIBDIR)

from aquilon.aqdb import depends
from aquilon.config import Config
from aquilon.aqdb.utils.confirm import confirm

from sqlalchemy                  import MetaData, engine, create_engine, text
from sqlalchemy.orm              import scoped_session, sessionmaker
from sqlalchemy.exceptions       import SQLError, DatabaseError as SaDBError
from sqlalchemy.ext.declarative  import declarative_base

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
        self.__dict__ = self.__shared_state

        try:
            self.config = Config()
        except Exception, e:
            print >> sys.stderr, "failed to read configuration: %s" % e
            sys.exit(os.EX_CONFIG)

        self.dsn = self.config.get('database', 'dsn')

        #extra care with prod when not running as cdb.
        #in prod on a reboot it may hang (waiting for input on stdin)
        #never tested that...

        prod_re = re.compile('@NYPO_AQUILON')
        if (prod_re.search(self.dsn) and
                    os.environ['USER'] != 'cdb'):

            msg='your DSN is on the production database, are you SURE? '
            if not confirm(prompt=msg, resp=False):
                print 'Thanks for playing, come again.'
                sys.exit(9)

        self.buf = StringIO()  #for mock engine output

        #ORACLE
        if self.dsn.startswith('oracle'):
            import cx_Oracle
            self.schema = self.config.get('database','dbuser')

            passwds = self._get_password_list()

            if len(passwds) < 1:
                passwds.append(
                    getpass(
                        'Can not determine your password (%s).\nPassword:'%(
                            self.dsn)))
            self.login(passwds)

        #DB2
        elif self.dsn.startswith('ibm_db_sa'):
            import ibm_db_sa
            import ibm_db_dbi

            user=''
            self.engine = create_engine(
                'ibm_db_sa:///NYTD_AQUILON?UID=%s'%(user))
            self.connection = self.engine.connect()
            self.engine.execute('set current schema AQUILON')

        #SQLITE
        elif self.dsn.startswith('sqlite'):
            self.engine = create_engine(self.dsn)
            self.connection = self.engine.connect()
        else:
            msg = "supported database datasources are db2, sqlite and oracle.\n"
            msg += "yours is '%s' "%(self.dsn)
            sys.stderr.write(msg)
            sys.exit(9)

        assert(self.dsn)
        assert(self.engine)

        self.meta   = MetaData(self.engine)
        assert(self.meta)

        self.Session = scoped_session(sessionmaker(bind=self.engine))
        assert(self.Session)

    def session(self):
        return self.Session()

    def login(self,passwds):
        errs = []
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
        """ convenience wrapper """
        res = self.safe_execute("SELECT id from %s where %s = :value"
                % (table, key), value=value)
        if res:
            rows = res.fetchall()
            if rows:
                return rows[0][0]
        return

    def buffer_output(self, s, p=""):
        return self.buf.write(s + p)

    def ddl(self, outfile=None):
        #TODO: reflect out the non-null constraints from oracle dbs (how???)
        mock_engine = create_engine(self.dsn, strategy='mock',
                                    executor=self.buffer_output)
        self.meta.reflect()
        self.meta.create_all(mock_engine)
        if outfile:
            with open(outfile, 'w') as f:
               f.write(self.buf.getvalue())
        else:
            print >> sys.stderr, self.buf.getvalue()

#ensure forward compatibility for proper class naming convention
#TODO: s/db_factory/DbFactory/g
DbFactory = db_factory


# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
