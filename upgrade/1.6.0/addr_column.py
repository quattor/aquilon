#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2013  Contributor
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
import sys

sys.path.insert(0, '../../lib/python2.6')
from aquilon.aqdb.dsdb import DsdbConnection
from aquilon.aqdb.db_factory import DbFactory
from aquilon.aqdb.utils.constraints import rename_non_null_check_constraints

dsdb = DsdbConnection()
dbf = DbFactory()

add_column = "ALTER TABLE building ADD address VARCHAR(255)"
dbf.engine.execute(add_column)

dsdb_select = "SELECT bldg_name, bldg_addr FROM bldg WHERE state >=0"

upd = """UPDATE building SET address=q'#{0}#' WHERE id=(
    SELECT id FROM location WHERE name='{1}' AND location_type='building') """

buildings = dsdb.run_query(dsdb_select)
for row in buildings.fetchall():
    try:
        dbf.engine.execute(upd.format(row[1], row[0]))
    except Exception, e:
        print e

#wipe redundant comments fields
upd = "update location set comments = NULL where location_type='building'"
try:
    dbf.engine.execute(upd)
except Exception, e:
    print e

#what about redundant fullname fields? pull the 5 character codes from FBI?
#or LDAP names?
null_addrs = """
SELECT L.NAME, B.ADDRESS
FROM  LOCATION L, BUILDING B
WHERE L.ID = B.ID
AND B.ADDRESS IS NULL""".lstrip()

no_addrs = dbf.engine.execute(null_addrs).fetchall()
if not no_addrs:
    nonnull="ALTER TABLE building MODIFY(address VARCHAR(255) NOT NULL)"
    dbf.engine.execute(nonnull)
    rename_non_null_check_constraints(dbf)
else:  #### If there are NULL addresses, they've probably been deleted in dsdb
    msg = "The following buildings have no address:\n%s" % no_addrs
    raise ValueError(msg)
