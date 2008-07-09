#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
import os

""" we'll be passing this to everything else. Do this first in case other
    modules have imports left over from early stage development. """

from db_factory import db_factory

dbf = db_factory()
print dbf.dsn
from depends import Base
Base.metadata.bind = dbf.engine

from depends import *
from debug import *
from admin import *

import table_maker

import migrate.changeset

def upgrade():
    ### STEP 1
    # Full export == safety net
    ##CHEATING here, losing patience
    DSN = 'cdb/cdb@LNPO_AQUILON_NY'
    exp = 'exp %s FILE=EXPORT/%s.dmp OWNER=%s DIRECT=n'%(DSN,
                                    dbf.schema, dbf.schema)
    exp += ' consistent=y statistics=none'.upper()

    print "%s"%(exp)
    msg = "\tis this the correct export statement? :"
    if not utils.confirm(prompt=msg, resp=False):
        print 'exiting.'
        sys.exit(1)

    print 'running %s'%(exp)
    rc = 0
    rc = os.system(exp)
    if rc != 0:
        print >>sys.stderr, "Command returned %d, aborting." % rc
        sys.exit(rc)

    # STEP 2: make the new stuff
    table_maker.upgrade(dbf)

#def downgrade():

""" A cheap downgrade script would be
    (1) run drop_tables_and_constraints()
    (2) run import
"""
if __name__ == '__main__':
    upgrade()
