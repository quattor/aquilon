#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" runs the update """

import sys
import os
import export

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(
                    DIR, '..', 'lib', 'python2.5')))
    import aquilon.aqdb.depends

from aquilon.aqdb.db_factory import db_factory, Base

dbf = db_factory()
Base.metadata.bind = dbf.engine

def upgrade(**kw):
    should_debug = kw.pop('debug', False)
    
    ### STEP 1: export with export.py
    #export.export()

    # STEP 2: destroy network table and rebuild
    #
    import update_network as n
    n.upgrade(dbf,debug=should_debug)

    # STEP 3: transform type_id FKs into table scalars
    files = ['mac_type_convert.py', 'loc_convert.py', 'system_convert.py']

    for f in files:
        execfile(f)

    # STEP 4: transform interface tables
    import interface_convert as ic
    ic.upgrade(dbf, debug=should_debug)

    # STEP 5: carry out the rest in natvice sql form the stmts file
    sqlfile = './sql_stmts'

    try:
        f = open(sqlfile, 'r')
    except IOError,e :
        print e
        sys.exit(9)

    for line in f:
        #debug('%s'%(line))
        if line.startswith('#') or line.isspace():
            continue
        else:
            dbf.safe_execute(line.strip(), debug=should_debug)
    

""" A cheap downgrade script would be
    (1) run drop_tables_and_constraints()
    (2) run import
"""
#def downgrade(*args, **kw):
#imp /tmp/cdb.dmp


if __name__ == '__main__':
    if '--debug' in sys.argv or '-d' in sys.argv:
        upgrade(debug=True)
    elif '--verbose' in sys.argv or '-v' in sys.argv:
        upgrade(verbose=True)
    else:
        upgrade()
