#!/ms/dist/python/PROJ/core/2.6.4-64/bin/python
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
