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

#import aquilon.aqdb.loc.location as loc
#import aquilon.aqdb.hw.interface as iface
#import aquilon.aqdb.sy.system    as sys

dbf = db_factory()
assert(dbf)

#tables = ['interface', 'location', 'machine', 'system']

tables = ['location']

for t in tables:
    stmt = 'select id, type from %s_type'%(t)

    rows = e.execute(stmt).fetchall()
    id2type = {}
    type2id = {}

    stmt = 'alter table %s add (%s_type varchar(32))'%(t, t)
    print stmt
    dbf.safe_execute(stmt)

    for row in rows:
        #print row
        id2type[row[0]] = row[1]
        type2id[row[1]] = row[0]
        #persist these for speed and longevity ???
    print id2type    

    col = 'location_type_id'

    for i in id2type.keys():
        upd = "update %s set %s_type = '%s' where %s = %d"%(
                t, t, id2type[i], col, i)
        dbf.safe_execute(upd, verbose=True)

    debug('---')

    drop = 'alter table %s drop column %s cascade constraints'%(t, col)

    dbf.safe_execute(drop, verbose=True)

    #add the NN constraint
    nn = """
alter table %s
    add constraint %s_type_nn
    check (('%s_type' is not null))"""%(t,t,t)

    dbf.safe_execute(nn.lstrip(), verbose=True)

    debug(' ')
