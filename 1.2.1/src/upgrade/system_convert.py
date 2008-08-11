#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" To convert type_id to type columns in 1.2.1 upgrade """
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(
        DIR, '..', 'lib', 'python2.5')))

    import aquilon.aqdb.depends

from sqlalchemy import engine, create_engine, text

#we're hardcoding this for use as the source database for all 'type' info
e = create_engine('oracle://cdb:cdb@LNPO_AQUILON_NY')
conn = e.connect()

assert e
assert conn

from aquilon.aqdb.db_factory import *

dbf = db_factory()
assert(dbf)

t = 'system'
col = 'system_type'

s1 = 'alter table %s add (%s varchar(32))'%(t, col)
dbf.safe_execute(s1, verbose=True)

s2 = 'select id, type from %s_type'%(t)
rows = e.execute(s2).fetchall()

id2type = {}
for row in rows:
    id2type[row[0]] = row[1]

for i in id2type.keys():
    upd = "update %s set %s = '%s' where type_id = %d"%(
        t, col, id2type[i], i)

    dbf.safe_execute(upd, verbose=True)

debug('---')

#delete the type_id column, ugly hack for busted system table column name
drop = 'alter table %s drop column type_id cascade constraints'%(t)

dbf.safe_execute(drop, verbose = True)

#add the NN constraint
nn = """
alter table %s
add constraint %s_nn
check (('%s' is not null))"""%(t, col, col)

dbf.safe_execute(nn.lstrip(), verbose=True )
debug(' ')

