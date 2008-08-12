#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Migrates network table from 1.2 to 1.2.1 """
import sys

def upgrade(dbf, **kw):
    should_debug = kw.pop('debug', False)
    #drop the table
    stmt = 'drop table network cascade constraints'

    dbf.safe_execute(stmt, debug=should_debug)

    if not should_debug:
        import aquilon.aqdb.net.network as n
        n.populate()
    else:
        print 'would have just run network.populate()'
        ##sys.exit(9)
