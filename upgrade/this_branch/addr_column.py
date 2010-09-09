#!/ms/dist/python/PROJ/core/2.6.4-64/bin/python
import sys

from ipy import ipy

sys.path.insert(0, '../../lib/python2.6')
from aquilon.aqdb.dsdb import DsdbConnection
from aquilon.aqdb.db_factory import DbFactory

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

nonnull="ALTER TABLE building MODIFY(address VARCHAR(255) NOT NULL)"
try:
    dbf.engine.execute(nonnull)
except Exception, e:
    print e

from aquilon.aqdb.utils.constraints import rename_non_null_check_constraints
rename_non_null_check_constraints(db)
