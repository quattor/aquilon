#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" intended to make the new tables during migration """

from depends import *

from new_tables.switch_port import SwitchPort, switch_port

new_tables = [ switch_port ]

# we *don't* want these dropped at the end.
#recreated  = [ network, service_instance ]

def upgrade(dbf):
    #tables = recreated + new_tables
    for t in new_tables:
        if hasattr(dbf, "schema"):
            t.schema = dbf.schema
        print t
        t.create(checkfirst=True)

def downgrade(dbf):
    for t in new_tables:
        if hasattr(dbf, "schema"):
            t.schema = dbf.schema
        print t
        t.drop(bind=dbf.engine,checkfirst=True)

#if __name__ == '__main__':
#    print dbf.dsn
#
#    upgrade()
#    downgrade()
