#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010  Contributor
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
