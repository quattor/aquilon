""" For Systems and related objects """

from datetime import datetime

from sqlalchemy import (Table, Integer, DateTime, Sequence, String, Column,
                        ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relation, deferred, backref
from sqlalchemy.ext.orderinglist import ordering_list

from aquilon.aqdb.model import Base, Host, CfgPath


class BuildItem(Base):
    """ Identifies the build process of a given Host.
        Parent of 'build_element' """
    __tablename__ = 'build_item'

    id = Column(Integer, Sequence('build_item_id_seq'), primary_key=True)

    host_id = Column('host_id', Integer, ForeignKey('host.id',
                                                     ondelete='CASCADE',
                                                     name='build_item_host_fk'),
                      nullable=False)

    cfg_path_id = Column(Integer, ForeignKey(
        'cfg_path.id', name='build_item_cfg_path_fk'), nullable=False)

    position = Column(Integer, nullable=False)
    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = deferred(Column(String(255), nullable=True))

    # Having lazy=False here is essential.  This outer join saves
    # thousands of queries whenever finding clients of a service
    # instance.
    host = relation(Host, backref='build_items', lazy=False)
    #TODO: auto-updated "last_used" column?
    cfg_path = relation(CfgPath, uselist=False, backref='build_items')


    def __repr__(self):
        return '%s: %s'%(self.host.name,self.cfg_path)

build_item = BuildItem.__table__

build_item.primary_key.name='build_item_pk'

build_item.append_constraint(
    UniqueConstraint('host_id', 'cfg_path_id', name='host_tmplt_uk'))

build_item.append_constraint(
    UniqueConstraint('host_id', 'position', name='host_position_uk'))

Host.templates = relation(BuildItem,
                         collection_class=ordering_list('position'),
                         order_by=['build_item.position'])

table = build_item

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
