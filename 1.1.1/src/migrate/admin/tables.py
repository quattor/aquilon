#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" functions related to tables """

import sys
sys.path.insert(0,'..')

from depends import *
from utils import confirm

def empty(table,dbf):
    """
        Returns True if no rows in table, helps in interative schema population
    """
    if  dbf.engine.execute(table.count()).fetchone()[0] < 1:
        return True
    else:
        return False

def get_table_list_from_db(dbf):
    """
    return a list of table names from the current
    databases public schema
    """
    sql='select table_name from user_tables'
    execute = dbf.engine.execute
    return [name for (name, ) in execute(text(sql))]

def get_seq_list_from_db(dbf):
    """return a list of the sequence names from the current
       databases public schema
    """
    sql='select sequence_name from user_sequences'
    execute = dbf.engine.execute
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
        for table in get_table_list_from_db(dbf):
            try:
                execute(
                    text('DROP TABLE %s CASCADE CONSTRAINTS' %(table)))
            except SQLError, e:
                print >> sys.stderr, e

        for seq in get_seq_list_from_db(dbf):
            try:
               execute(text('DROP SEQUENCE %s'%(seq)))
            except SQLError, e:
                print >> sys.stderr, e
