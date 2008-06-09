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

############   REMOVE WHEN USED AS A LIBRARY   ##
import db_factory                               #
dbf = db_factory.db_factory()                   #
Base.metadata.bind = dbf.engine                 #
#################################################

from new_tables.role import Role,role
from new_tables.host_list import HostList, host_list
from new_tables.location_search_list import LocationSearchList, location_search_list
from new_tables.host_list_item import HostListItem, host_list_item
from new_tables.network import network
from new_tables.service_instance import service_instance

new_tables = [ role, location_search_list, host_list, host_list_item ]

# we *don't* want these dropped at the end.
recreated  = [ network, service_instance ]

def upgrade():
    tables = recreated + new_tables
    for t in new_tables:
            if dbf.schema:
                t.schema = dbf.schema
                print t
                t.create()

def downgrade():
    for t in new_tables:
            if dbf.schema:
                t.schema = dbf.schema
                print t
                t.drop(bind=dbf.engine)

if __name__ == '__main__':
    print dbf.dsn

    upgrade()
    downgrade()
