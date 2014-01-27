# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""To be imported by classes and modules requiring aqdb access"""

import re
import os
import sys
import logging
from numbers import Number

from aquilon.aqdb import depends
from aquilon.config import Config
from aquilon.utils import monkeypatch
from aquilon.exceptions_ import AquilonError

from sqlalchemy.exc import DatabaseError
from sqlalchemy import MetaData, create_engine, text, event
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.schema import CreateIndex, Sequence
from sqlalchemy.dialects.oracle.base import OracleDDLCompiler


# Add support for Oracle-specific index extensions
@compiles(CreateIndex, 'oracle')
def visit_create_index(create, compiler, **kw):
    index = create.element
    compiler._verify_index_table(index)
    preparer = compiler.preparer

    text = "CREATE "
    if index.unique:
        text += "UNIQUE "
    if index.kwargs.get("oracle_bitmap", False):
        text += "BITMAP "

    text += "INDEX %s ON %s (%s)" \
        % (compiler._prepared_index_name(index, include_schema=True),
           preparer.format_table(index.table, use_schema=True),
           ', '.join(compiler.sql_compiler.process(expr, include_table=False)
                     for expr in index.expressions))

    compress = index.kwargs.get("oracle_compress", False)
    if compress:
        if isinstance(compress, Number):
            text += " COMPRESS %d" % compress
        else:
            text += " COMPRESS"

    return text


# Add support for table compression
@monkeypatch(OracleDDLCompiler)
def post_create_table(self, table):
    text = ""
    compress = table.kwargs.get("oracle_compress", False)
    if compress:
        if isinstance(compress, basestring):
            text += " COMPRESS FOR " + compress.upper()
        else:
            text += " COMPRESS"

    return text


def sqlite_foreign_keys(dbapi_con, con_record):
    dbapi_con.execute('pragma foreign_keys=ON')


def sqlite_no_fsync(dbapi_con, con_record):
    dbapi_con.execute('pragma synchronous=OFF')


def oracle_set_module(dbapi_con, con_record):
    # Store the program's name in v$session. Trying to set a value longer than
    # the allowed length will generate ORA-24960, so do an explicit truncation.
    prog = os.path.basename(sys.argv[0])
    dbapi_con.module = prog[:48]


def oracle_reset_action(dbapi_con, con_record):
    # Reset action and clientinfo in v$session. The DB connection may be closed
    # when this function is called, so be careful.
    if dbapi_con is None:
        return
    try:
        dbapi_con.action = ""
        dbapi_con.clientinfo = ""
    except:
        pass


class DbFactory(object):
    __shared_state = {}
    __started = False  # at the class definition, that is

    def __init__(self, *args, **kw):
        self.__dict__ = self.__shared_state

        if self.__started:
            return

        self.__started = True

        config = Config()
        log = logging.getLogger(__name__)

        if config.has_option("database", "module"):
            from ms.modulecmd import Modulecmd, ModulecmdExecError

            module = config.get("database", "module")
            cmd = Modulecmd()
            try:
                log.info("Loading module %s." % module)
                cmd.load(module)
            except ModulecmdExecError, err:
                log.error("Failed to load module %s: %s" % (module, err))

        self.dsn = config.get('database', 'dsn')

        self.pool_options = {}
        self.pool_options["pool_size"] = config.getint("database", "pool_size")
        self.pool_options["max_overflow"] = config.getint("database",
                                                          "pool_max_overflow")
        if len(config.get("database", "pool_timeout").strip()) > 0:
            self.pool_options["pool_timeout"] = config.getint("database",
                                                              "pool_timeout")
        else:
            self.pool_options["pool_timeout"] = None
        log.info("Database engine using pool options %s" % self.pool_options)

        passwds = self._get_password_list(config)

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
                log = logging.getLogger(__name__)
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

            # Events should be registered before we try to open a real
            # connection below, because the underlying DBAPI connection will not
            # be closed
            if self.engine.dialect.name == "oracle":
                event.listen(self.engine, "connect", oracle_set_module)
                event.listen(self.no_lock_engine, "connect", oracle_set_module)
                event.listen(self.engine, "checkin", oracle_reset_action)
                event.listen(self.no_lock_engine, "checkin",
                             oracle_reset_action)

            try:
                connection = self.engine.connect()
                connection.close()
                return
            except DatabaseError, e:
                errs.append(e)

        if errs:
            raise errs.pop()
        else:
            raise AquilonError('Failed to connect to %s')

    def _get_password_list(self, config):
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

    def get_sequences(self):
        """ return a list of the sequence names from the current databases
            public schema  """

        query = None
        if self.engine.dialect.name == 'oracle':
            query = text("SELECT sequence_name FROM user_sequences")
            return [name for (name, ) in self.engine.execute(query)]
        elif self.engine.dialect.name == 'postgresql':
            query = text("SELECT relname FROM pg_class WHERE relkind = 'S'")
            return [name for (name, ) in self.engine.execute(query)]

    def drop_all_tables_and_sequences(self):  # pragma: no cover
        """ MetaData.drop_all() doesn't play nice with db's that have sequences.
            Your alternative is to call this """
        config = Config()
        if self.engine.dialect.name == 'sqlite':
            dbfile = config.get("database", "dbfile")
            if os.path.exists(dbfile):
                os.unlink(dbfile)
        elif self.engine.dialect.name == 'oracle':
            for table in inspect(self.engine).get_table_names():
                # We can't use bind variables with DDL
                stmt = text('DROP TABLE "%s" CASCADE CONSTRAINTS' %
                            self.engine.dialect.denormalize_name(table))
                self.engine.execute(stmt)
            for seq_name in self.get_sequences():
                seq = Sequence(seq_name)
                seq.drop(bind=self.engine)

            self.engine.execute(text("PURGE RECYCLEBIN"))
        elif self.engine.dialect.name == 'postgresql':
            for table in inspect(self.engine).get_table_names():
                # We can't use bind variables with DDL
                stmt = text('DROP TABLE "%s" CASCADE' % table)
                self.engine.execute(stmt, table=table)
            for seq_name in self.get_sequences():
                seq = Sequence(seq_name)
                seq.drop(bind=self.engine)

            # Should we issue VACUUM?
        else:
            raise ValueError('Can not drop %s databases' %
                             self.engine.dialect.name)
