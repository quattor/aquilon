#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Fill in later"""

from datetime import datetime
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import (Column, Table, Integer, Sequence, String, DateTime,
                        ForeignKey, UniqueConstraint, Index)
from sqlalchemy.orm import relation, deferred, backref
from sqlalchemy.ext.orderinglist import ordering_list

from aquilon.aqdb.db_factory         import Base
from aquilon.aqdb.sy.system          import System
from aquilon.aqdb.sy.system_list     import SystemList

class SystemListItem(Base):
    __tablename__ = 'system_list_item'

    system_list_id = Column(Integer, ForeignKey(
        'system_list.id', ondelete = 'CASCADE', name = 'sys_li_sl_fk'),
                          primary_key = True)

    system_id = Column(Integer, ForeignKey(
        'system.id', ondelete = 'CASCADE', name = 'sli_system_fk'),
                          primary_key = True)

    position        = Column(Integer, nullable = False)

    creation_date   = deferred(Column(DateTime, default = datetime.now,
                                      nullable = False))
    comments        = deferred(Column(String(255), nullable = True))

    system          = relation(System, backref = 'systemlist_items')
    systemlist      = relation(SystemList, uselist = False,
                               backref = 'systemlist')

    def __str__(self):
        return str(self.system.name)

    def __repr__(self):
        return self.__class__.__name__ + " " + str(self.system.name)

system_list_item = SystemListItem.__table__

system_list_item.primary_key.name = 'system_list_item_pk'

system_list_item.append_constraint(
    UniqueConstraint('system_id', name = 'system_list_item_uk')) #one list only?

#TODO: would we like this mapped in system_list.py instead?
SystemList.sytems = relation(SystemListItem,
                            collection_class=ordering_list('position'),
                            order_by=[SystemListItem.__table__.c.position])

def populate(*args, **kw):
    from aquilon.aqdb.db_factory import db_factory, Base
    from sqlalchemy import insert

    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    if 'debug' in args:
        Base.metadata.bind.echo = True
    s = dbf.session()

    system_list_item.create(checkfirst = True)

    if Base.metadata.bind.echo == True:
        Base.metadata.bind.echo == False
