#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" A collection of table level functions for maintenance """

from confirm import confirm
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import text

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

def drop_all_tables_and_sequences(dbf):
    """ MetaData.drop_all() doesn't play nice with db's that have sequences.
        you're alternative is to call this"""
    if not dbf.dsn.startswith('ora'):
        print 'dsn is not oracle, exiting'
        return False
    msg="You've asked to wipe out the %s database. Please confirm."%(dbf.dsn)

    if confirm(prompt=msg, resp=False):
        execute = dbf.engine.execute
        for table in get_table_list_from_db(dbf.engine):
            try:
                execute(text('DROP TABLE %s CASCADE CONSTRAINTS' %(table)))
            except SQLError, e:
                print >> sys.stderr, e

        for seq in get_seq_list_from_db(dbf.engine):
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
