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

from new_tables.role import Role, role, populate as populate_role
from new_tables.host_list import HostList, host_list
from new_tables.location_search_list import (
    LocationSearchList, location_search_list)
from new_tables.host_list_item import HostListItem, host_list_item
from new_tables.network import network
from new_tables.service_instance import service_instance
from new_tables.search_list_item import SearchListItem

new_tables = [ role, location_search_list, host_list, host_list_item,
              search_list_item ]

# we *don't* want these dropped at the end.
recreated  = [ network, service_instance ]
location = Table('location', Base.metadata, autoload=True)
network = Table('network', Base.metadata, autoload=True)
network_type = Table('network_type', Base.metadata, autoload = True)
service = Table('service', Base.metadata, autoload=True)
cfg_path = Table('cfg_path', Base.metadata, autoload=True)
netmask = Table('netmask', Base.metadata, autoload = True)

def upgrade(dbf):
    tables = recreated + new_tables
    for t in tables:
            if dbf.schema:
                t.schema = dbf.schema
                print t
                t.create(checkfirst=True)
    populate_role(dbf)

def downgrade(dbf):
    for t in tables:
            if dbf.schema:
                t.schema = dbf.schema
                print t
                t.drop(bind=dbf.engine,checkfirst=True)

#if __name__ == '__main__':
#    print dbf.dsn
#
#    upgrade()
#    downgrade()
