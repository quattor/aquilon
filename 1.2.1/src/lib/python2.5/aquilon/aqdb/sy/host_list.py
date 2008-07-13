#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Lists of hosts are a system type"""


from datetime import datetime
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from aquilon.aqdb.db_factory         import Base
from aquilon.aqdb.table_types.name_table import make_name_class


#TODO: this is a polymorphic subtype of System...
HostList = make_name_class('HostList','host_list')
host_list = HostList.__table__
host_list.primary_key.name = 'host_list_pk'

def populate():
    from aquilon.aqdb.db_factory import db_factory, Base
    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    Base.metadata.bind.echo = True
    s = dbf.session()

    host_list.create(checkfirst = True)

##This will go into HostListItem for now...
#HostList.hosts = relation(HostListItem,
#                          collection_class=ordering_list('position'),
#                            order_by=[HostListItem.__table__.c.position])
#host_list_item=HostListItem.__table__
#host_list_item.create(checkfirst=True)
