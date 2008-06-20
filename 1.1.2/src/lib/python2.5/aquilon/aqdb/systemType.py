#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""  The discriminator for Systems """
import sys
sys.path.append('../..')
#from aqdbBase import aqdbBase
#from db_factory import db_factory
from db import meta, engine, Base
import subtypes as st

from sqlalchemy import select

SystemType  = st.subtype('SystemType','system_type')
system_type = SystemType.__table__
def get_sys_type_id(typ_nm):
    """ To keep session out of __init__ methods for systems """
    sl=select([system_type.c.id], system_type.c.type=='%s'%(typ_nm))
    return engine.execute(sl).fetchone()[0]

_sys_types = ['base_system_type', 'host', 'afs_cell', 'quattor_server',
              'tor_switch']

if __name__ == '__main__':
    #dbf = db_factory()
    #aqdbBase.metadata.bind = dbf.engine
    system_type.create(checkfirst=True)

    st.populate_subtype(SystemType, _sys_types)
