#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" collection of utilities for oracle sequences """
#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" Pull out resources and actions from introspection of aqd/aqdb code"""
import os
import sys


import db_factory
dbf = db_factory.db_factory()
engine = dbf.engine
execute = engine.execute

#TODO: make iterable to replace maps with safe_ in
#get_table_names + seqs
def safe_execute(stmt):
    try:
        execute(text(stmt))
    except SQLError, e:
        print >> sys.stderr, e

def get_table_names():
    """
    return a list of table names from the current
    databases public schema
    """
    sql='select table_name from user_tables'

    return [name for (name, ) in execute(text(sql))]

def get_seqs():
    from sqlalchemy.sql import text
    """return a list of the sequence names from the current
       databases public schema
    """
    sql='select sequence_name from user_sequences'

    return [name for (name, ) in execute(text(sql))]

def drop_seq(seq):
    safe_execute('DROP SEQUENCE %s'%(seq))

def drop_seq_list():
    for seq in get_seq_list():
        drop_seq(seq)


"""
A demo

    m = dbf.meta

    m.reflect()
    sq_list = get_seqs()
    for t in m.table_iterator():
        max= mk_seq_as_max_id(t)
        if max:
            sq_name = t.name.upper()+'_ID_SEQ'
            print '%s (%s): %s'%(t.name,sq_name,mk_seq_as_max_id(t)),
            create = 'CREATE SEQUENCE %s start with %s'%(sq_name,max)
            print '    %s'%(create)
            print
"""
