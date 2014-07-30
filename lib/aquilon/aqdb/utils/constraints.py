# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
""" Functions for managing Oracle constraints """

from __future__ import print_function
import re

from sqlalchemy.sql import text

_long_nms = {}
_long_nms['CHASSIS_MANAGER'] = 'CHAS_MGR'
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
_long_nms['CLUSTER_REQUIRED'] = 'CLSTR_REQ'
_long_nms['METACLUSTER_ID'] = 'MTACLSTR_ID'
_long_nms['METACLUSTER_MEMBER'] = 'MTACLSTR_MBR'
_long_nms['ESX_CLUSTER'] = 'ESX_CLSTR'
_long_nms['ESX_CLUSTER_ID'] = 'ESX_CLSTR_ID'
_long_nms['ESX_CLUSTER_MEMBER'] = 'ESX_CLSTR_MBR'
_long_nms['CLUSTER_SERVICE_BINDING'] = 'CLSTR_SVC_BNDG'
_long_nms['HOST_CLUSTER_MEMBER'] = 'HOST_CLSTR_MMBR'
_long_nms['MACHINE_SPECS'] = 'MCHN_SPECS'
_long_nms['CONTROLLER_TYPE'] = 'CNTRLR_TYPE'
_long_nms['CREATION_DATE'] = 'CR_DATE'
_long_nms['USER_PRINCIPAL_ID'] = 'USR_PRNC_ID'
_long_nms['OPERATING_SYSTEM'] = 'OS'
_long_nms['DOWN_HOSTS_THRESHOLD'] = 'DOWN_HOSTS_THR'
_long_nms['PERSONALITY_CLUSTER_INFO'] = 'PERS_CLSTR'
_long_nms['PERSONALITY_CLUSTER_INFO_ID'] = 'PERS_CLSTRID'
_long_nms['PERSONALITY_ESX_CLUSTER_INFO'] = 'PERS_ESXCLSTR'
_long_nms['VMHOST_OVERCOMMIT_MEMORY'] = 'VM_OVRCMT_MEM'
_long_nms['HIGH_AVAILABILITY'] = 'HA'
_long_nms['VLAN_INTERFACE_ID'] = 'VLAN_IFACE_ID'
_long_nms['ADDRESS_ASSIGNMENT'] = 'ADDR_ASSIGN'
_long_nms['DNS_ENVIRONMENT_ID'] = 'DNS_ENV_ID'
_long_nms['NETWORK_ENVIRONMENT'] = 'NET_ENV'
_long_nms['NETWORK_ENVIRONMENT_ID'] = 'NET_ENV_ID'
_long_nms['REQUIRES_CHANGE_MANAGER'] = 'REQ_CHG_MGR'
_long_nms['PERSONALITY_GRN_MAP'] = 'PERS_GRN_MAP'
_long_nms['SERVICE_ADDRESS'] = 'SRV_ADDR'
_long_nms['REBUILD_REQUIRED'] = 'REBLD_REQ'
_long_nms['HOST_ENVIRONMENT_ID'] = 'HOST_ENV_ID'
_long_nms['NETWORK_DEVICE_ID'] = 'NETDEV_ID'
_long_nms['PERSONALITY_ROOTUSER'] = 'PERS_ROOT_USER'
_long_nms['PERSONALITY_ROOTNETGROUP'] = 'PERS_ROOT_NG'
_long_nms['LOCATION_CONSTRAINT_ID'] = 'LOC_CONSTR_ID'


def rename_non_null_check_constraints(db):
    stmt = text("""
    SELECT C.constraint_name  con,
           C.table_name       tab,
           C.search_condition cond
      FROM user_constraints C
     WHERE C.constraint_type = 'C'
       AND C.constraint_name LIKE 'SYS_C00%' """)

    result = db.engine.execute(stmt)

    rename = []
    pat = re.compile('\"(.*)\"')

    for (constraint, table, condition) in result:
        if condition.endswith('IS NOT NULL'):
            col = pat.match(condition).group().strip('"')

            # Replace the column name if its long
            if col in _long_nms:
                col = _long_nms[col]

            # Replace table name if its long
            if table in _long_nms:
                new_name = '%s_%s_NN' % (_long_nms[table], col)
            else:
                new_name = '%s_%s_NN' % (table, col)

            if len(new_name) > 30:
                print("Renaming %s to %s would fail, new name longer than 32 "
                      "characters" % (constraint, new_name))
                continue

            rename = text('ALTER TABLE "%s" RENAME CONSTRAINT "%s" TO "%s"' %
                          (table, constraint, new_name))
            db.engine.execute(rename)
