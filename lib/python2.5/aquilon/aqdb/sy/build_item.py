#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" For Systems and related objects """

from datetime import datetime
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import (Table, Integer, DateTime, Sequence, String, select,
                        Column, ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relation, deferred, backref
from sqlalchemy.ext.orderinglist import ordering_list

from aquilon.aqdb.db_factory    import Base
from aquilon.aqdb.cfg.cfg_path  import CfgPath
from aquilon.aqdb.sy.host       import Host


class BuildItem(Base):
    """ Identifies the build process of a given Host.
        Parent of 'build_element' """
    __tablename__ = 'build_item'

    id       = Column(Integer, Sequence('build_item_id_seq'), primary_key=True)

    host_id  = Column('host_id', Integer, ForeignKey(
        'host.id', ondelete='CASCADE',
        name='build_item_host_fk'), nullable = False)

    cfg_path_id = Column(Integer, ForeignKey(
        'cfg_path.id', name='build_item_cfg_path_fk'), nullable = False)

    position      = Column(Integer, nullable = False)
    creation_date = deferred(Column(DateTime, default = datetime.now,
                                    nullable = False))
    comments      = deferred(Column(String(255), nullable = True))

    host     = relation(Host, backref = 'build_items')
    #TODO: auto-updated "last_used" column?
    cfg_path = relation(CfgPath, uselist = False, backref = 'build_items') #TODO: backref?


    def __repr__(self):
        return '%s: %s'%(self.host.name,self.cfg_path)

build_item = BuildItem.__table__

build_item.primary_key.name = 'build_item_pk'

build_item.append_constraint(
    UniqueConstraint('host_id', 'cfg_path_id', name = 'host_tmplt_uk'))

build_item.append_constraint(
    UniqueConstraint('host_id', 'position', name = 'host_position_uk'))

Host.templates = relation(BuildItem,
                         collection_class = ordering_list('position'),
                         order_by = ['build_item.position'])

table = build_item

#def populate(db, *args, **kw):
    #s = db.session()
    #build_item.create(checkfirst = True)

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-

