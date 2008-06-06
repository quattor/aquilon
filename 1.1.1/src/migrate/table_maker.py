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

from IPython.Shell import IPShellEmbed
ipshell = IPShellEmbed()

import db_factory
dbf = db_factory.db_factory()

Base.metadata.bind = dbf.engine

from role import Role,role
from host_list import HostList, host_list
from location_search_list import LocationSearchList, location_search_list
from host_list_item import HostListItem, host_list_item

new_tables = [ role, location_search_list, host_list, host_list ]
#def get_tables_with_schema ?

if __name__ == '__main__':
    print dbf.dsn

    for t in new_tables:
        if dbf.schema:
            t.schema = dbf.schema
        print t

    #ipshell()
