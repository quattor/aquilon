# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016  Contributor
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
import time
import hashlib
import struct

from aquilon.aqdb import depends  # pylint: disable=W0611
from aquilon.config import Config
from aquilon.exceptions_ import AquilonError

from sqlalchemy.exc import DatabaseError
from sqlalchemy import create_engine, text, event
from sqlalchemy.engine.url import make_url
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.schema import Sequence

# Global cache of SQL statement hashes, used to implement unique query plan
# logging
query_hashes = None


def sqlite_foreign_keys(dbapi_con, con_record):  # pylint: disable=W0613
    dbapi_con.execute('pragma foreign_keys=ON')


def sqlite_no_fsync(dbapi_con, con_record):  # pylint: disable=W0613
    dbapi_con.execute('pragma synchronous=OFF')


def sqlite_show_plan(conn, cursor, statement, parameters, context, executemany):
    # pylint: disable=W0613
    sqlid = stmt_2_sqlid(statement)
    if query_hashes is not None:
        if sqlid in query_hashes:
            return
        query_hashes.add(sqlid)

    explain = "EXPLAIN QUERY PLAN " + statement
    if executemany:
        cursor.executemany(explain, parameters)
    elif not parameters:
        cursor.execute(explain)
    else:
        cursor.execute(explain, parameters)

    log = logging.getLogger(__name__)
    rows = cursor.fetchall()
    for row in rows:
        log.info("Plan: %s", "|".join(str(col) for col in row))


def stmt_2_sqlid(stmt):
    # Generate Oracle SQL_ID for an SQL statement.
    # Based on http://www.slaviks-blog.com/2010/03/30/oracle-sql_id-and-hash-value/
    hash = hashlib.md5(stmt + '\x00').digest()
    _, _, msb, lsb = struct.unpack('IIII', hash)
    sqln = long(msb) * (2 ** 32) + lsb
    alphabet = '0123456789abcdfghjkmnpqrstuvwxyz'
    sqlid = ''
    while sqln:
        sqlid = alphabet[sqln % 32] + sqlid
        sqln //= 32

    if len(sqlid) < 13:
        sqlid = "0" * (13 - len(sqlid)) + sqlid

    return sqlid


def oracle_set_module(dbapi_con, con_record):  # pylint: disable=W0613
    # Store the program's name in v$session. Trying to set a value longer than
    # the allowed length will generate ORA-24960, so do an explicit truncation.
    prog = os.path.basename(sys.argv[0])
    dbapi_con.module = prog[:48]


def oracle_reset_action(dbapi_con, con_record):  # pylint: disable=W0613
    # Reset action and clientinfo in v$session. The DB connection may be closed
    # when this function is called, so be careful.
    if dbapi_con is None:
        return
    try:
        dbapi_con.action = ""
        dbapi_con.clientinfo = ""
    except:
        pass


def oracle_enable_statistics(dbapi_con, con_record):  # pylint: disable=W0613
    log = logging.getLogger(__name__)
    stmt = 'ALTER SESSION SET statistics_level = all'
    cursor = dbapi_con.cursor()
    log.info(stmt)
    cursor.execute(stmt)
    cursor.close()


def oracle_remember_sqlid(conn, cursor, statement, parameters, context,
                          executemany):
    # pylint: disable=W0613
    if statement.lower().startswith("set "):
        return
    sqlid = stmt_2_sqlid(statement)
    if query_hashes is not None:
        if sqlid in query_hashes:
            return
        query_hashes.add(sqlid)

    context._oracle_sqlid = sqlid


def oracle_show_plan(conn, cursor, statement, parameters, context, executemany):
    # pylint: disable=W0613
    if not hasattr(context, "_oracle_sqlid"):
        return

    log = logging.getLogger(__name__)
    dbapi_conn = conn.connection.connection
    cursor2 = dbapi_conn.cursor()
    cursor2.execute("SELECT plan_table_output "
                    "FROM table(dbms_xplan.display_cursor(:sqlid, NULL, 'typical'))",
                    sqlid=context._oracle_sqlid)
    rows = cursor2.fetchall()
    for row in rows:
        log.info("Plan: %s", row[0])
    cursor2.close()
    delattr(context, "_oracle_sqlid")


def oracle_set_default_schema(dbapi_con, con_record):  # pylint: disable=W0613
    log = logging.getLogger(__name__)
    config = Config()
    schema = config.get("database", "default_schema")
    stmt = 'ALTER SESSION SET current_schema = ' + schema
    cursor = dbapi_con.cursor()
    log.info(stmt)
    cursor.execute(stmt)
    cursor.close()


def postgres_show_plan(conn, cursor, statement, parameters, context, executemany):
    # pylint: disable=W0613
    cmd = statement.split()[0]
    if cmd.upper() not in ("SELECT", "INSERT", "UPDATE", "DELETE"):
        return

    sqlid = stmt_2_sqlid(statement)
    if query_hashes is not None:
        if sqlid in query_hashes:
            return
        query_hashes.add(sqlid)

    log = logging.getLogger(__name__)

    cursor.execute("SAVEPOINT explain_plan")
    try:
        explain = "EXPLAIN ANALYZE VERBOSE " + statement
        if executemany:
            cursor.executemany(explain, parameters)
        elif not parameters:
            cursor.execute(explain)
        else:
            cursor.execute(explain, parameters)

        rows = cursor.fetchall()
        for row in rows:
            log.info("Plan: %s", row[0])
    except Exception as err:
        log.error("Error fetching plan: %s", err)
    finally:
        cursor.execute("ROLLBACK TO SAVEPOINT explain_plan")
        cursor.execute("RELEASE SAVEPOINT explain_plan")


def postgres_set_default_schema(dbapi_con, con_record):  # pylint: disable=W0613
    log = logging.getLogger(__name__)
    config = Config()
    schema = config.get("database", "default_schema")
    stmt = 'SET search_path TO %s,public' % schema
    cursor = dbapi_con.cursor()
    log.info(stmt)
    cursor.execute(stmt)
    cursor.close()


def timer_start(conn, cursor, statement, parameters, context, executemany):
    # pylint: disable=W0613
    conn.info.setdefault('query_start_time', []).append(time.time())


def timer_stop(conn, cursor, statement, parameters, context, executemany):
    # pylint: disable=W0613
    total = time.time() - conn.info['query_start_time'].pop(-1)
    log = logging.getLogger(__name__)
    log.info("Query running time: %f", total)


class DbFactory(object):
    __shared_state = {}
    __started = False  # at the class definition, that is

    def create_engine(self, config, dsn, **pool_options):
        engine = create_engine(dsn, **pool_options)
        show_plan = config.has_option("database", "log_query_plans") and \
            config.getboolean("database", "log_query_plans")
        if config.has_option("database", "log_unique_plans_only") and \
           config.getboolean("database", "log_unique_plans_only"):
            global query_hashes
            query_hashes = set()

        if engine.dialect.name == "oracle":
            event.listen(engine, "connect", oracle_set_module)
            event.listen(engine, "checkin", oracle_reset_action)
            if config.has_option("database", "default_schema"):
                event.listen(engine, "connect", oracle_set_default_schema)
            if show_plan:
                event.listen(engine, "connect", oracle_enable_statistics)
                event.listen(engine, "before_cursor_execute", oracle_remember_sqlid)
                event.listen(engine, "after_cursor_execute", oracle_show_plan)
        elif engine.dialect.name == "sqlite":
            event.listen(engine, "connect", sqlite_foreign_keys)
            if config.has_option("database", "disable_fsync") and \
               config.getboolean("database", "disable_fsync"):
                event.listen(engine, "connect", sqlite_no_fsync)
                log = logging.getLogger(__name__)
                log.info("SQLite is operating in unsafe mode!")
            if show_plan:
                event.listen(engine, "before_cursor_execute", sqlite_show_plan)
        elif engine.dialect.name == "postgresql":
            if config.has_option("database", "default_schema"):
                event.listen(engine, "connect", postgres_set_default_schema)
            if show_plan:
                event.listen(engine, "before_cursor_execute", postgres_show_plan)

        if self.verbose:
            engine.echo = True

        if config.has_option("database", "log_query_times") and \
           config.getboolean("database", "log_query_times"):
            event.listen(engine, "before_cursor_execute", timer_start)
            event.listen(engine, "after_cursor_execute", timer_stop)

        return engine

    def __init__(self, verbose=False):
        self.__dict__ = self.__shared_state

        if self.__started:
            return

        self.__started = True
        self.verbose = verbose

        config = Config()
        log = logging.getLogger(__name__)

        if config.has_option("database", "module"):
            from ms.modulecmd import Modulecmd, ModulecmdExecError

            module = config.get("database", "module")
            cmd = Modulecmd()
            try:
                log.info("Loading module %s.", module)
                cmd.load(module)
            except ModulecmdExecError as err:
                log.error("Failed to load module %s: %s", module, err)

        pool_options = {}

        for optname in ("pool_size", "pool_timeout", "pool_recycle"):
            if config.has_option("database", optname):
                if len(config.get("database", optname).strip()) > 0:
                    pool_options[optname] = config.getint("database", optname)
                else:
                    # pool_timeout can be set to None
                    pool_options[optname] = None

        # Sigh. max_overflow does not start with pool_*
        if config.has_option("database", "pool_max_overflow"):
            pool_options["max_overflow"] = config.getint("database",
                                                         "pool_max_overflow")
        log.info("Database engine using pool options %s", pool_options)

        dsn = config.get('database', 'dsn')
        dialect = make_url(dsn).get_dialect()

        if dialect.name == "oracle":
            self.login(config, dsn, pool_options)
        elif dialect.name == "postgresql":
            self.login(config, dsn, pool_options)
        elif dialect.name == "sqlite":
            self.engine = self.create_engine(config, dsn)
            self.no_lock_engine = None
            connection = self.engine.connect()
            connection.close()
        else:
            raise AquilonError("Supported database datasources are postgresql, "
                               "oracle and sqlite. You've asked for: %s" %
                               dialect.name)

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

    def login(self, config, raw_dsn, pool_options):
        # Default: no password
        passwords = [""]
        pswd_re = re.compile('PASSWORD')

        if config.has_option("database", "password_file"):
            passwd_file = config.get("database", "password_file")
            if passwd_file:
                with open(passwd_file) as f:
                    passwords = [line.strip() for line in f]

                if not passwords:
                    raise AquilonError("Password file %s is empty." %
                                       passwd_file)

        errs = []
        for p in passwords:
            dsn = re.sub(pswd_re, p, raw_dsn)
            self.engine = self.create_engine(config, dsn, **pool_options)
            self.no_lock_engine = self.create_engine(config, dsn,
                                                     **pool_options)

            try:
                connection = self.engine.connect()
                connection.close()
                return
            except DatabaseError as e:
                errs.append(e)

        if errs:
            raise errs.pop()
        else:
            raise AquilonError('Failed to connect to %s' % raw_dsn)

    def get_sequences(self):  # pragma: no cover
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


def db_prompt(session):
    """
    Return a string describing the database connection.

    There are no assumptions about the format, other than it should be
    relatively short and descriptive, so it can be used as part of a
    command-line prompt.
    """
    engine = session.bind

    if engine.dialect.name == 'sqlite':
        prompt = str(engine.url).split('///')[1]
    elif engine.dialect.name == 'oracle':  # pragma: no cover
        stmt = "SELECT sys_context('userenv', 'session_user') FROM DUAL"
        user = session.execute(stmt).scalar()
        stmt = "SELECT sys_context('userenv', 'current_schema') FROM DUAL"
        schema = session.execute(stmt).scalar()
        stmt = "SELECT sys_context('userenv', 'instance_name') FROM DUAL"
        instance = session.execute(stmt).scalar()
        stmt = "SELECT sys_context('userenv', 'db_name') FROM DUAL"
        dbname = session.execute(stmt).scalar()

        if user != schema:
            prompt = '%s@%s/%s[%s]' % (user, instance, dbname, schema)
        else:
            prompt = '%s@%s/%s' % (user, instance, dbname)
    elif engine.dialect.name == 'postgresql':  # pragma: no cover
        stmt = "SELECT current_user"
        user = session.execute(stmt).scalar()
        host = engine.url.host or ""
        stmt = "SELECT current_database()"
        dbname = session.execute(stmt).scalar()
        prompt = '%s@%s/%s' % (user, host, dbname)
    else:  # pragma: no cover
        raise AquilonError("Unknown database dialect: %s." % engine.dialect.name)

    return prompt
