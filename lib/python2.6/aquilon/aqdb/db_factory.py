# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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

from aquilon.aqdb import depends
from aquilon.config import Config
from aquilon.utils import confirm, monkeypatch
from aquilon.exceptions_ import AquilonError

from sqlalchemy import MetaData, create_engine, text, event
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.exc import DBAPIError, DatabaseError as SaDBError
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


def sqlite_foreign_keys(dbapi_con, con_record):
    dbapi_con.execute('pragma foreign_keys=ON')


def sqlite_no_fsync(dbapi_con, con_record):
    dbapi_con.execute('pragma synchronous=OFF')


class DbFactory(object):
    __shared_state = {}
    __started = False  # at the class definition, that is

    def __init__(self, *args, **kw):
        self.__dict__ = self.__shared_state

        if self.__started:
            return

        self.__started = True

        self.dsn = config.get('database', 'dsn')

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

        passwds = self._get_password_list()

        # ORACLE
        if self.dsn.startswith('oracle'):
            import cx_Oracle  # pylint: disable=W0612

            self.login(passwds)

        # POSTGRESQL
        elif self.dsn.startswith('postgresql'):
            import psycopg2  # pylint: disable=W0612

            self.login(passwds)

        # SQLITE
        elif self.dsn.startswith('sqlite'):
            self.engine = create_engine(self.dsn)
            self.no_lock_engine = None
            event.listen(self.engine, "connect", sqlite_foreign_keys)
            if config.has_option("database", "disable_fsync") and \
               config.getboolean("database", "disable_fsync"):
                event.listen(self.engine, "connect", sqlite_no_fsync)
                log = logging.getLogger('aqdb.db_factory')
                log.info("SQLite is operating in unsafe mode!")
            connection = self.engine.connect()
            connection.close()
        else:
            msg = "Supported database datasources are postgresql, oracle and sqlite.\n"
            msg += "yours is '%s' " % self.dsn
            sys.stderr.write(msg)
            sys.exit(9)

        self.meta = MetaData(self.engine)
        assert self.meta

        self.Session = scoped_session(sessionmaker(bind=self.engine))
        assert self.Session

        # For database types that support concurrent connections, we
        # create a separate thread pool for connections that promise
        # not to wait on locks.
        if self.no_lock_engine:
            self.NLSession = scoped_session(sessionmaker(
                bind=self.no_lock_engine))
        else:
            self.NLSession = self.Session

    def login(self, passwds):
        errs = []
        pswd_re = re.compile('PASSWORD')
        dsn_copy = self.dsn

        if not passwds:
            raise AquilonError("At least one password must be specified, even "
                               "if that's empty.")

        for p in passwds:
            self.dsn = re.sub(pswd_re, p, dsn_copy)
            self.engine = create_engine(self.dsn, **self.pool_options)
            self.no_lock_engine = create_engine(self.dsn, **self.pool_options)

            try:
                connection = self.engine.connect()
                connection.close()
                return
            except SaDBError, e:
                errs.append(e)

        if errs:
            raise errs.pop()
        else:
            raise AquilonError('Failed to connect to %s')

    def _get_password_list(self):
        """
        Read a password file containing one password per line. The passwords
        will be tried in the order they appear in the file.
        """

        # Default: no password
        if not config.has_option("database", "password_file") or \
           not config.get("database", "password_file").strip():
            return [""]

        passwd_file = config.get("database", "password_file")
        if not os.path.exists(passwd_file):
            raise AquilonError("The password file '%s' does not exist." %
                               passwd_file)

        passwds = ""
        with open(passwd_file) as f:
            passwds = f.readlines()
            if not passwds:
                raise AquilonError("Password file %s is empty." % passwd_file)

        return [passwd.strip() for passwd in passwds]

    def safe_execute(self, stmt, **kw):
        """ convenience wrapper """
        try:
            return self.engine.execute(text(stmt), **kw)
        except DBAPIError, e:
            print >> sys.stderr, e

    def get_tables(self):
        """ return a list of table names from the current databases public
        schema """

        if self.engine.dialect.name == 'oracle':
            sql = 'select table_name from user_tables'
            return [name for (name, ) in self.safe_execute(sql)]
        elif self.engine.dialect.name == 'postgresql':
            sql = "select table_name from information_schema.tables " \
                    "where table_schema='public'"
            return [name for (name, ) in self.safe_execute(sql)]

    def get_sequences(self):
        """ return a list of the sequence names from the current databases
            public schema  """

        if self.engine.dialect.name == 'oracle':
            sql = 'select sequence_name from user_sequences'
            return [name for (name, ) in self.safe_execute(sql)]
        elif self.engine.dialect.name == 'postgresql':
            sql = "select sequence_name from information_schema.sequences " \
                    "where sequence_schema='public'"
            return [name for (name, ) in self.safe_execute(sql)]

    def drop_all_tables_and_sequences(self, no_confirm=False):  # pragma: no cover
        """ MetaData.drop_all() doesn't play nice with db's that have sequences.
            you're alternative is to call this """
        if self.engine.dialect.name == 'sqlite':
            dbfile = config.get("database", "dbfile")
            if os.path.exists(dbfile):
                os.unlink(dbfile)
        elif self.engine.dialect.name == 'oracle':
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
        elif self.engine.dialect.name == 'postgresql':
            # Don't show the password
            dbname = re.sub(':.*@', '@', self.dsn)
            msg = ("\nYou've asked to wipe out the \n%s\ndatabase.  Please confirm."
                   % dbname)

            if no_confirm or confirm(prompt=msg, resp=False):
                for table in self.get_tables():
                    self.safe_execute('DROP TABLE "%s" CASCADE' % table)

                for seq in self.get_sequences():
                    self.safe_execute('DROP SEQUENCE "%s" CASCADE' % seq)

                # Should we issue VACUUM?
        else:
            raise ValueError('can not drop %s databases' %
                             self.engine.dialect.name)


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
