#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" Lists of hosts as a host type"""

import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from aquilon.aqdb.db_factory             import Base
from aquilon.aqdb.table_types.name_table import make_name_class

HostList = make_name_class('HostList','host_list')
host_list = HostList.__table__
host_list.primary_key.name = 'host_list_pk'

table = host_list

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-

