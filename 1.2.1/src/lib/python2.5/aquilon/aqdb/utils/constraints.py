#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" functions for managing Oracle constraints """

import re
import sys
import os

#if __name__ == '__main__':
DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
import aquilon.aqdb.db_factory as db_factory

#TODO:
    #double check we're not touching FKs... looked like we might be
    #refactor to do ALL constraint types with name like 'SYS_C00%'

_long_nms = {}
_long_nms['LOCATION_SEARCH_LIST']    = 'LOC_SRCH_LST'
_long_nms['LOCATION_SEARCH_LIST_ID'] = 'LOC_SRCH_LIST_ID'
_long_nms['SEARCH_LIST_ITEM']        = 'SRCH_LI'
_long_nms['SYSTEM_LIST_ITEM']        = 'SYSTEM_LI'
_long_nms['PHYSICAL_INTERFACE']      = 'PHYS_IFACE'
_long_nms['SERVICE_MAP']             = 'SVC_MAP'
_long_nms['SERVICE_LIST_ITEM']       = 'SVC_LI'
_long_nms['SERVICE_INSTANCE']        = 'SVC_INST'
_long_nms['CREATION_DATE']           = 'CR_DATE'

def rename_sys_pks(dbf):
    stmt = """
    SELECT C.constraint_name  con,
           C.table_name       tab,
           C.search_condition cond
      FROM user_constraints C
     WHERE C.constraint_type = 'P'
       AND C.constraint_name LIKE 'SYS_C00%' """

    cons = dbf.safe_execute(stmt)

    if cons:
        for i in cons:
            #print i
            nm = '%s_pk'%(i[1])
            rename = 'ALTER TABLE %s RENAME CONSTRAINT %s to %s'%(
                i[1], i[0], nm)
            db_factory.debug(rename)
            dbf.safe_execute(rename)
    else:
        print 'PKs are all properly named'

def rename_non_null_check_constraints(dbf):
    stmt = """
    SELECT C.constraint_name  con,
           C.table_name       tab,
           C.search_condition cond
      FROM user_constraints C
     WHERE C.constraint_type = 'C'
       AND C.constraint_name LIKE 'SYS_C00%' """

    cons = dbf.safe_execute(stmt)

    rename =[]
    pat = re.compile('\"(.*)\"')

    for i in cons:
        if i[2].endswith('IS NOT NULL'):
            col = pat.match(i[2]).group().strip('"')
            if col in _long_nms.keys():
                col = _long_nms[col]
            #TODO: replace with table_info in next version
            if i[1] in _long_nms.keys():
                nm = '%s_%s_NN'%(_long_nms[i[1]], col)
            else:
                nm = '%s_%s_NN'%(i[1], col)

            rename = 'ALTER TABLE %s RENAME CONSTRAINT %s TO %s'%(i[1],i[0],nm)

            if len(nm) > 30:
                print '%s\n would fail, new name longer than 32 characters'%(
                    rename)
                continue
            else:
                db_factory.debug(rename)
                dbf.safe_execute(rename)

"""
LNPO_AQUILON_NY> select distinct constraint_type from user_constraints;

CONSTRAINT_TYPE
---------------
R (references AKA foreign key)
U (unique)
P (primary key)
C (check constraint (like non null))
"""
