# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015  Contributor
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

import re

from sqlalchemy.sql import text

from aquilon.exceptions_ import AquilonError

# It would be nice to have this information as part of the definitions of the
# tables/classes instead of one giant table here, but that would not work: the
# names of constraints referencing other tables may need to be calculated when
# the remote table has not been defined yet, so the Table objects cannot be used
# to store the information.
_table_abbrev = {
    'address_assignment': 'addr_assign',
    'archetype': 'arch',
    'cluster_service_binding': 'clstr_svc_bndg',
    'dns_environment': 'dns_env',
    'dns_record': 'dnsrec',
    'hardware_entity': 'hw_ent',
    'host_cluster_member': 'host_clstr_mmbr',
    'host_environment': 'host_env',
    'interface': 'iface',
    'metacluster': 'mtaclstr',
    'metacluster_member': 'mtaclstr_mbr',
    'netgroup_whitelist': 'netgr_whtlst',
    'network_device': 'netdev',
    'network_environment': 'net_env',
    'network_compartment': 'net_comp',
    'operating_system': 'os',
    'param_definition': 'param_def',
    'param_def_holder': 'pd_holder',
    'personality': 'pers',
    'personality_cluster_info': 'pers_clstr',
    'personality_esx_cluster_info': 'pers_esxclstr',
    'personality_grn_map': 'pers_grn_map',
    'personality_rootuser': 'pers_rootuser',
    'personality_rootnetgroup': 'pers_rootng',
    'personality_service_list_item': 'psli',
    'personality_service_map': 'pers_svc_map',
    'personality_stage': 'pers_st',
    'reboot_intervention': 'reboot_iv',
    'service': 'svc',
    'service_address': 'srv_addr',
    'service_address_interface': 'srv_addr_iface',
    'service_instance': 'svc_inst',
    'service_instance_server': 'sis',
    'service_list_item': 'sli',
    'virtual_switch': 'vswitch',
}

_col_abbrev = {
    'cluster_required': 'clstr_req',
    'controller_type': 'ctrl_type',
    'creation_date': 'cr_date',
    'high_availability': 'ha',
    'location_constraint_id': 'loc_constr_id',
    'rebuild_required': 'rebld_req',
    'requires_change_manager': 'req_chg_mgr',
    'vmhost_overcommit_memory': 'vm_ovrcmt_mem',
}


def ref_constraint_name(local_table, remote_table=None, column=None, suffix=None):
    # Oracle has a rather small limit on identifier names, so we need to
    # abbreviate. The logic we use for abbreviation:
    # - Abbreviate only when it's needed, use the full table/column name if it
    #   fits inside the limit
    # - Abbreviate from right to left. In this case, it means trying to
    #   abbreviate the column name first, if that's not enough then the remote
    #   table, if even that's not enough then the local table name.

    local_abbrev = _table_abbrev.get(local_table, local_table)

    if remote_table:
        remote_abbrev = _table_abbrev.get(remote_table, remote_table)
    else:
        remote_abbrev = None

    if column:
        col_abbrev = _col_abbrev.get(column, column)
    else:
        col_abbrev = None

    # Try to abbreviate from the right: first the column, then the remote table,
    # lastly the local table.
    for local in (local_table, local_abbrev):
        for remote in (remote_table, remote_abbrev):
            for col in (column, col_abbrev):
                # Ignore empty components
                items = [item for item in (local, remote, col) if item]

                items.append(suffix)
                name = "_".join(items)
                if len(name) <= 30:
                    return name

    raise AquilonError("Cannot abbreviate (%s, %s, %s)" %
                       (local_table, remote_table, column))


def multi_col_constraint_name(table_name, columns, suffix):
    col_names = []
    for name, col in columns.items():
        # If the column looks like a reference to a remote table, then use the
        # name of the remote object. It's not really a table name in all cases,
        # but that's not a problem.
        if name.endswith('_id') and col.foreign_keys:
            col_names.append(name[:-3])
        else:
            col_names.append(name)

    name = '%s_%s_%s' % (table_name, "_".join(col_names), suffix)
    if len(name) <= 30:
        return name

    # Try to abbreviate column names
    col_names = []
    for name, col in columns.items():
        # If the column looks like a reference to another table, then try to
        # abbreviate the remote table name.
        if name.endswith('_id') and col.foreign_keys:
            rtable = name[:-3]
            col_names.append(_table_abbrev.get(rtable, rtable))
        else:
            col_names.append(_col_abbrev.get(name, name))

    name = '%s_%s_%s' % (table_name, "_".join(col_names), suffix)
    if len(name) <= 30:
        return name

    # Try to abbreviate the local table name too
    name = '%s_%s_%s' % (_table_abbrev.get(table_name, table_name),
                         "_".join(col_names), suffix)
    if len(name) <= 30:
        return name

    raise AquilonError("Cannot abbreviate (%s, %s)" %
                       (table_name, ", ".join(list(columns.keys))))


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

    for (constraint, orig_table, condition) in result:
        if not condition.endswith('IS NOT NULL'):
            continue

        table = orig_table.lower()
        col = pat.match(condition).group().strip('"').lower()

        # If the column looks like a reference to a remote table, then try to
        # abbreviate both the local and the remote table name. This is just
        # heuristics, since we do not check for foreign keys here.
        if col.endswith("_id") and col not in _col_abbrev:
            rtable, rcol = col.rsplit("_", 1)
            new_name = ref_constraint_name(table, rtable, rcol, 'nn')
        else:
            new_name = ref_constraint_name(table, None, col, 'nn')

        rename = text('ALTER TABLE "%s" RENAME CONSTRAINT "%s" TO "%s"' %
                      (orig_table, constraint, new_name.upper()))
        db.engine.execute(rename)
