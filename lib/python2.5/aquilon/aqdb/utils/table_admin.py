""" A collection of table level functions for maintenance """

from confirm import confirm

from sqlalchemy import text
from sqlalchemy.exceptions import SQLError

def get_table_list_from_db(engine):
    """
    return a list of table names from the current
    databases public schema
    """
    sql='select table_name from user_tables'
    execute = engine.execute
    return [name for (name, ) in execute(text(sql))]

def get_seq_list_from_db(engine):
    """return a list of the sequence names from the current
       databases public schema
    """
    sql='select sequence_name from user_sequences'
    execute = engine.execute
    return [name for (name, ) in execute(text(sql))]

def drop_all_tables_and_sequences(db,option=None):
    """ MetaData.drop_all() doesn't play nice with db's that have sequences.
        you're alternative is to call this"""
    if not db.dsn.startswith('ora'):
        pass

    if db.dsn.endswith('@NYPO_AQUILON'):
        sys.stderr.write(
            'your DSN is on the production database, not permitted \n')
        sys.exit(9)

    msg = ("\nYou've asked to wipe out the \n%s\ndatabase.  Please confirm."
           % db.dsn)

    if confirm(prompt=msg, resp=False):
        execute = db.engine.execute
        for table in get_table_list_from_db(db.engine):
            try:
                execute(text('DROP TABLE %s CASCADE CONSTRAINTS' %(table)))
            except SQLError, e:
                print >> sys.stderr, e

        for seq in get_seq_list_from_db(db.engine):
            try:
                execute(text('DROP SEQUENCE %s'%(seq)))
            except SQLError, e:
                print >> sys.stderr, e

        try:
            execute(text('PURGE RECYCLEBIN'))
        except SQLError, e:
            print >> sys.stderr, e

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
