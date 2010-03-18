# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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
""" functions for managing Oracle constraints """

import re

#TODO:
    #double check we're not touching FKs... looked like we might be
    #refactor to do ALL constraint types with name like 'SYS_C00%'

_long_nms = {}
_long_nms['CHASSIS_MANAGER'] = 'CHAS_MGR'
_long_nms['TOR_SWITCH'] = 'TOR_SW'
_long_nms['HARDWARE_ENTITY_TYPE'] = 'HW_ENT_TYP'
_long_nms['HARDWARE_ENTITY_TYPE_ID'] = 'HW_ENT_TYP_ID'
_long_nms['HARDWARE_ENTITY'] = 'HW_ENT'
_long_nms['HARDWARE_ENTITY_ID'] = 'HW_ENT_ID'
_long_nms['LOCATION_SEARCH_LIST'] = 'LOC_SRCH_LST'
_long_nms['LOCATION_SEARCH_LIST_ID'] = 'LOC_SRCH_LIST_ID'
_long_nms['SEARCH_LIST_ITEM'] = 'SRCH_LI'
_long_nms['SYSTEM_LIST_ITEM'] = 'SYSTEM_LI'
_long_nms['CONSOLE_SERVER_ID'] = 'CONS_SVR_ID'
_long_nms['INTERFACE'] = 'IFACE'
_long_nms['SERVICE_ID'] = 'SVC_ID'
_long_nms['SERVICE_MAP'] = 'SVC_MAP'
_long_nms['SERVICE_LIST_ITEM'] = 'SVC_LI'
_long_nms['SERVICE_INSTANCE'] = 'SVC_INST'
_long_nms['SERVICE_INSTANCE_ID'] = 'SVC_INST_ID'
_long_nms['SERVICE_INSTANCE_SERVER'] = 'SIS'
_long_nms['PERSONALITY_ID'] = 'PRSNLTY_ID'
_long_nms['PERSONALITY_SERVICE_LIST_ITEM'] = 'PRSNLTY_SLI'
_long_nms['PERSONALITY_SERVICE_MAP'] = 'PRSNLTY_SVC_MAP'
_long_nms['CREATION_DATE'] = 'CR_DATE'
_long_nms['USER_PRINCIPAL_ID'] = 'USR_PRNC_ID'
_long_nms['CLUSTER_TYPE'] = 'CLSTR_TYP'
_long_nms['CLUSTER_ALIGNED_SERVICE'] = 'CLSTR_ALND_SVC'
_long_nms['METACLUSTER_ID'] = 'MTACLSTR_ID'
_long_nms['METACLUSTER_MEMBER'] = 'MTACLSTR_MBR'
_long_nms['ESX_CLUSTER'] = 'ESX_CLSTR'
_long_nms['ESX_CLUSTER_ID'] = 'ESX_CLSTR_ID'
_long_nms['ESX_CLUSTER_MEMBER'] = 'ESX_CLSTR_MBR'
_long_nms['CLUSTER_SERVICE_BINDING'] = 'CLSTR_SVC_BNDG'
_long_nms['MACHINE_CLUSTER_MEMBER'] = 'MCHN_CLSTR_MMBR'
_long_nms['HOST_CLUSTER_MEMBER'] = 'HOST_CLSTR_MMBR'
_long_nms['MACHINE_SPECS'] = 'MCHN_SPECS'
_long_nms['CONTROLLER_TYPE'] = 'CNTRLR_TYPE'
_long_nms['CREATION_DATE']           = 'CR_DATE'
_long_nms['USER_PRINCIPAL_ID']       = 'USR_PRNC_ID'
_long_nms['OPERATING_SYSTEM'] = 'OS'
_long_nms['DOWN_HOSTS_THRESHOLD'] = 'THRSH'


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
            #replace the column name if its long
            if col in _long_nms.keys():
                col = _long_nms[col]
            #replace table name if its long
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

#
