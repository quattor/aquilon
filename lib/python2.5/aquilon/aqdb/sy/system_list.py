#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" Lists of systems as a system type"""

import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from aquilon.aqdb.db_factory             import Base
from aquilon.aqdb.table_types.name_table import make_name_class

SystemList = make_name_class('SystemList','system_list')
system_list = SystemList.__table__
system_list.primary_key.name = 'system_list_pk'

table = system_list

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-

