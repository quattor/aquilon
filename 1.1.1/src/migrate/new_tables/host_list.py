#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Copied from code base 1.1.1 for migration """
from depends import *

class HostList(Base):
    __tablename__= 'host_list'

    id = Column(Integer, Sequence('host_list_id_seq'), primary_key = True)
    name = Column('name', String(32), unique = True, nullable = False)

    creation_date = Column('creation_date', DateTime,
           default=datetime.now, nullable = False)

    comments = Column('comments', String(255), nullable = True)

host_list = HostList.__table__

#These need a physical table to take place ...
#    Perform after create or run as alter/rename in migrate.changeset

#host_list.append_constraint(
#    PrimaryKeyConstraint(host_list.c.id, name = 'host_list_pk'))
#
#host_list.append_constraint(
#    UniqueConstraint(host_list.c.name, name = 'host_list_uk'))
