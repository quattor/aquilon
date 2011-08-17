# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""To be imported by classes and modules requiring aqdb access"""

import re
import os
import sys
import logging

from getpass import getpass
from StringIO import StringIO

from aquilon.aqdb import depends
from aquilon.config import Config
from aquilon.utils import confirm, monkeypatch

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.exceptions import SQLError, DatabaseError as SaDBError
from sqlalchemy.interfaces import PoolListener
from sqlalchemy.schema import CreateIndex
from sqlalchemy.dialects.oracle.base import OracleDDLCompiler

import ms.modulecmd as modcmd

try:
    config = Config()
except Exception, e:
    print >> sys.stderr, 'failed to read configuration: %s' % e
    sys.exit(os.EX_CONFIG)

assert config, 'No configuration in db_factory'

if config.has_option("database", "module"):
    modcmd.load(config.get("database", "module"))


# Add support for Oracle-specific index extensions
@compiles(CreateIndex, 'oracle')
def visit_create_index(create, compiler, **kw):
    index = create.element
    preparer = compiler.preparer

    text = "CREATE "
    if index.unique:
        text += "UNIQUE "
    if index.kwargs.get("oracle_bitmap", False):
        text += "BITMAP "

    # FIXME: this is really a per-column property, but Index.__init__ does not
    # accept column expressions like "sqlalchemy.sql.desc(some_table.c.col)"
    if index.kwargs.get("oracle_desc", False):
        dirtxt = " DESC"
    else:
        dirtxt = ""

    text += "INDEX %s ON %s (%s)" \
            % (preparer.quote(compiler._index_identifier(index.name),
                              index.quote),
               preparer.format_table(index.table),
               ', '.join(preparer.quote(c.name, c.quote) + dirtxt
                         for c in index.columns))

    if index.kwargs.get("oracle_compress", False):
        text += " COMPRESS"

    return text


# Add support for table compression
@monkeypatch(OracleDDLCompiler)
def post_create_table(self, table):
    if table.kwargs.get("oracle_compress", False):
        return " COMPRESS"
    return ""


class ForeignKeySQLiteListener(PoolListener):
    def connect(self, dbapi_con, con_record):
        dbapi_con.execute('pragma foreign_keys=ON')

class UnsafeSQLiteListener(PoolListener):
    def connect(self, dbapi_con, con_record):
        dbapi_con.execute('pragma synchronous=OFF')


class DbFactory(object):
    __shared_state = {}
    __started = False # at the class definition, that is

    def __init__(self, *args, **kw):
        self.__dict__ = self.__shared_state

        if self.__started:
            return

        self.__started = True

        self.dsn = config.get('database', 'dsn')
        assert self.dsn, 'No DSN in db_factory'

        self.pool_options = {}
        self.pool_options["pool_size"] = config.getint(
            "database", "pool_size")
        self.pool_options["max_overflow"] = config.getint("database",
                                                          "pool_max_overflow")
        if len(config.get("database", "pool_timeout").strip()) > 0:
            self.pool_options["pool_timeout"] = config.getint("database",
                                                              "pool_timeout")
        else:
            self.pool_options["pool_timeout"] = None
        log = logging.getLogger('aqdb.db_factory')
        log.info("Database engine using pool options %s" % self.pool_options)

        #ORACLE
        if self.dsn.startswith('oracle'):
            import cx_Oracle
            self.vendor = 'oracle'
            self.schema = config.get('database','dbuser')

            if self.schema != '':
                passwds = self._get_password_list()

                if not passwds:
                    msg = "No passwords found for %s." % self.dsn
                    print >> sys.stderr, msg
                    sys.exit(0)
                self.login(passwds)
            else:
                #we're kerberized
                self.kerberized = True
                self.engine = create_engine(self.dsn, **self.pool_options)
                connection = self.engine.connect()
                connection.close()

        #SQLITE
        elif self.dsn.startswith('sqlite'):
            listeners = [ForeignKeySQLiteListener()]
            if config.has_option("database", "disable_fsync") and \
               config.getboolean("database", "disable_fsync"):
                listeners.append(UnsafeSQLiteListener())
                log = logging.getLogger('aqdb.db_factory')
                log.info("SQLite is operating in unsafe mode!")

            self.engine = create_engine(self.dsn, listeners=listeners)
            connection = self.engine.connect()
            connection.close()
            self.vendor = 'sqlite'
        else:
            msg = "supported database datasources are sqlite and oracle.\n"
            msg += "yours is '%s' "% (self.dsn)
            sys.stderr.write(msg)
            sys.exit(9)

        assert self.dsn, 'No dsn in DbFactory.__init__'
        assert self.engine, 'No engine in DbFactory.__init__'

        self.meta   = MetaData(self.engine)
        assert self.meta

        self.Session = scoped_session(sessionmaker(bind=self.engine))
        assert self.Session

        # For database types that support concurrent connections, we
        # create a separate thread pool for connections that promise
        # not to wait on locks.
        if hasattr(self, "no_lock_engine"):
            self.NLSession = scoped_session(sessionmaker(
                bind=self.no_lock_engine))
        else:
            self.NLSession = self.Session

    def login(self, passwds):
        errs = []
        pswd_re = re.compile('PASSWORD')
        dsn_copy = self.dsn

        for p in passwds:
            self.dsn = re.sub(pswd_re, p, dsn_copy)
            self.engine = create_engine(self.dsn, **self.pool_options)

            try:
                connection = self.engine.connect()
                connection.close()
                self.no_lock_engine = create_engine(self.dsn,
                                                    **self.pool_options)
                return
            except SaDBError, e:
                errs.append(e)

        if len(errs) >= 1:
            raise errs.pop()
        else:
            msg = 'unknown issue connecting to %s'% (self.dsn)
            raise SaDBError(msg)

    def _get_password_list(self):
        """ searches through PTS protected directory structure for file,
            which is multiline list of *all* passwords in age order descending
            (i.e. newest on top). It will try them sequentially, finally
            giving up and throwing an exception """

        if config.has_option("database", "dbpassword"):
            #TODO: RAISE WARNING: we'd like to get out of that buisness I think
            return [config.get("database", "dbpassword")]
        else:
            passwd_file = config.get("database", "password_file")
            passwds = []

            try:
                f = open(passwd_file)
                passwds = f.readlines()
                if len(passwds) < 1:
                    msg = "No lines in %s"% (passwd_file)
                    raise ValueError(msg)
                else:
                    return [passwd.strip() for passwd in passwds]
            # Fallback for testing when password file may not exist.
            except IOError, e:
                print e
                return None

    def safe_execute(self, stmt, **kw):
        """ convenience wrapper """
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

    def get_tables(self):
        """ return a list of table names from the current databases public
        schema """

        if self.vendor is 'oracle':
            sql = 'select table_name from user_tables'
            return [name for (name, ) in self.safe_execute(sql)]

    def get_sequences(self):
        """ return a list of the sequence names from the current databases
            public schema  """

        sql = 'select sequence_name from user_sequences'
        return [name for (name, ) in self.safe_execute(sql)]

    def drop_all_tables_and_sequences(self, no_confirm=False):  # pragma: no cover
        """ MetaData.drop_all() doesn't play nice with db's that have sequences.
            you're alternative is to call this """
        if self.vendor is 'sqlite':
            dbfile = config.get("database", "dbfile")
            if os.path.exists(dbfile):
                os.unlink(dbfile)

        elif self.vendor is not 'oracle':
            raise ValueError('can not drop %s databases'%(self.vendor))

        if is_prod_ora_instance(self.dsn):
            msg = 'drop_all_tables not permitted on the production database'
            raise ValueError(msg)

        # Don't show the password
        dbname = re.sub(':.*@', '@', self.dsn)
        msg = ("\nYou've asked to wipe out the \n%s\ndatabase.  Please confirm."
               % dbname)

        if no_confirm or confirm(prompt=msg, resp=False):
            for table in self.get_tables():
                self.safe_execute('DROP TABLE "%s" CASCADE CONSTRAINTS' % table)

            for seq in self.get_sequences():
                self.safe_execute('DROP SEQUENCE "%s"' % seq)

            self.safe_execute('PURGE RECYCLEBIN')

def is_prod_ora_instance(dsn):  # pragma: no cover
    prod_re = re.compile('@NYPO_AQUILON', re.IGNORECASE)
    if prod_re.search(dsn):
        return True
    else:
        return False

def is_prod_user():  # pragma: no cover
    if os.environ['USER'] == 'cdb':
        return True
    else:
        return False

def is_prod(dsn):  # pragma: no cover
    if is_prod_ora_instance(dsn) and is_prod_user():
        return True
    else:
        return False
