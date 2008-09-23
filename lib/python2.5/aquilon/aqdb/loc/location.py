#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" If you can read this you should be documenting """

from datetime import datetime
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import (Table, Integer, DateTime, Sequence, String, select,
                        Column, ForeignKey, UniqueConstraint, text)

from sqlalchemy.orm import deferred, relation, backref, object_session

from aquilon.aqdb.db_factory import Base
from aquilon.aqdb.column_types.aqstr import AqStr


class Location(Base):
    __tablename__ = 'location'

    id = Column(Integer, Sequence('location_id_seq'), primary_key=True)

    name = Column(AqStr(16), nullable = False)

    parent_id = Column(Integer, ForeignKey(
        'location.id', name='loc_parent_fk'), nullable = True)

    location_type = Column(AqStr(32), nullable = False)

    #KEEP FOR BACKWARDS COMPATIBILITY FOR NOW...

    #location_type_id = Column(Integer, ForeignKey(
    #    'location_type.id', ondelete = 'CASCADE',
    #    name = 'sli_loc_typ__fk'), nullable = False)

    fullname = Column(String(255), nullable = False)

    creation_date = deferred(Column(DateTime, default = datetime.now,
                                    nullable = False))
    comments = deferred(Column(String(255), nullable = True))

    __mapper_args__ = {'polymorphic_on' : location_type}

    def get_parents(loc):
        pl=[]
        p_node=loc.parent
        if not p_node:
            return pl
        while p_node.parent is not None and p_node.parent != p_node:
            pl.append(p_node)
            p_node=p_node.parent
        pl.append(p_node)
        pl.reverse()
        return pl

    def get_p_dict(loc):
        d={}
        p_node=loc
        while p_node.parent is not None and p_node.parent != p_node:
            d[str(p_node.location_type)]=p_node
            p_node=p_node.parent
        return d

    def _parents(self):
        return self.get_parents()
    parents = property(_parents)

    def _p_dict(self):
        return self.get_p_dict()
    p_dict = property(_p_dict)

    def _hub(self):
        return self.p_dict.get('hub', None)
    hub = property(_hub)

    def _continent(self):
        return self.p_dict.get('continent', None)
    continent=property(_continent)

    def _country(self):
        return self.p_dict.get('country', None)
    country = property(_country)

    def _city(self):
        return self.p_dict.get('city', None)
    city = property(_city)

    def _building(self):
        return self.p_dict.get('building', None)
    building = property(_building)

    def _rack(self):
        return self.p_dict.get('rack', None)
    rack = property(_rack)

    def _chassis(self):
        return self.p_dict.get('chassis', None)
    chassis = property(_chassis)

    def append(self,node):
        if isinstance(node, Location):
            node.parent = self
            self.sublocations[node] = node

    def sysloc(self):
        if str(self.location_type) in ['building','rack','chassis','desk']:
            return str('.'.join([str(self.p_dict[item]) for item in
                ['building', 'city', 'continent']]))

    def _children(self):
        s = text("""select * from location
                    where id != %d
                    connect by parent_id = prior id
                    start with id = %d"""%(self.id,self.id))

        return object_session(self).query(Location).from_statement(s).all()

    children = property(_children)

    def typed_children(self,typ):
        s = text("""select * from location
                    where location_type = '%s'
                    connect by parent_id = prior id
                    start with id = %d"""%(typ, self.id))

        return object_session(self).query(Location).from_statement(s).all()

    def __repr__(self):
        return self.__class__.__name__ + " " + str(self.name)

    def __str__(self):
        return str(self.name)

location = Location.__table__

location.primary_key.name = 'location_pk'

location.append_constraint(
    UniqueConstraint('name', 'location_type', name='loc_name_type_uk'))

Location.sublocations = relation('Location', backref = backref(
        'parent', remote_side=[location.c.id],))

table = location

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
