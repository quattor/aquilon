""" functions for managing Oracle constraints """

import re

#TODO:
    #double check we're not touching FKs... looked like we might be
    #refactor to do ALL constraint types with name like 'SYS_C00%'

_long_nms = {}
_long_nms['CHASSIS_MANAGER']         = 'CHAS_MGR'
_long_nms['TOR_SWITCH']              = 'TOR_SW'
_long_nms['HARDWARE_ENTITY_TYPE']    = 'HW_ENT_TYP'
_long_nms['HARDWARE_ENTITY_TYPE_ID'] = 'HW_ENT_TYP_ID'
_long_nms['HARDWARE_ENTITY']         = 'HW_ENT'
_long_nms['HARDWARE_ENTITY_ID']      = 'HW_ENT_ID'
_long_nms['LOCATION_SEARCH_LIST']    = 'LOC_SRCH_LST'
_long_nms['LOCATION_SEARCH_LIST_ID'] = 'LOC_SRCH_LIST_ID'
_long_nms['SEARCH_LIST_ITEM']        = 'SRCH_LI'
_long_nms['SYSTEM_LIST_ITEM']        = 'SYSTEM_LI'
_long_nms['CONSOLE_SERVER_ID']       = 'CONS_SVR_ID'
_long_nms['INTERFACE']               = 'IFACE'
_long_nms['SERVICE_MAP']             = 'SVC_MAP'
_long_nms['SERVICE_LIST_ITEM']       = 'SVC_LI'
_long_nms['SERVICE_INSTANCE']        = 'SVC_INST'
_long_nms['SERVICE_INSTANCE_SERVER'] = 'SIS'
_long_nms['CREATION_DATE']           = 'CR_DATE'
_long_nms['USER_PRINCIPAL_ID']       = 'USR_PRNC_ID'

def rename_sys_pks(db, *args, **kw):
    stmt = """
    SELECT C.constraint_name  con,
           C.table_name       tab,
           C.search_condition cond
      FROM user_constraints C
     WHERE C.constraint_type = 'P'
       AND C.constraint_name LIKE 'SYS_C00%' """

    cons = db.safe_execute(stmt)

    if cons:
        for i in cons:
            #print i
            nm = '%s_pk'%(i[1])
            rename = 'ALTER TABLE %s RENAME CONSTRAINT %s to %s'%(
                i[1], i[0], nm)
            dbf.debug(rename)
            db.safe_execute(rename)
    else:
        print 'PKs are all properly named'

def rename_non_null_check_constraints(db, debug=False, *args, **kw):
    stmt = """
    SELECT C.constraint_name  con,
           C.table_name       tab,
           C.search_condition cond
      FROM user_constraints C
     WHERE C.constraint_type = 'C'
       AND C.constraint_name LIKE 'SYS_C00%' """

    cons = db.safe_execute(stmt)

    rename =[]
    pat = re.compile('\"(.*)\"')

    for i in cons:
        if i[2].endswith('IS NOT NULL'):
            col = pat.match(i[2]).group().strip('"')
            if col in _long_nms.keys():
                col = _long_nms[col]
            #TODO: replace with table_info in next version: look up abreviation in metadata tbl
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
                #TODO: use an integer value or the logger
                if(debug):
                    dbf.debug(rename)

                db.safe_execute(rename)

"""
LNPO_AQUILON_NY> select distinct constraint_type from user_constraints;

CONSTRAINT_TYPE
---------------
R (references AKA foreign key)
U (unique)
P (primary key)
C (check constraint (like non null))
"""

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
