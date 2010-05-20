# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
""" How we represent location data in Aquilon """

from datetime import datetime
from collections import deque

from sqlalchemy import (Integer, DateTime, Sequence, String, Column,
                        ForeignKey, UniqueConstraint, text)

from sqlalchemy.orm import relation, backref, object_session

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Base
from aquilon.aqdb.column_types import AqStr


class Location(Base):
    """ How we represent location data in Aquilon """
    __tablename__ = 'location'

    id = Column(Integer, Sequence('location_id_seq'), primary_key=True)

    name = Column(AqStr(16), nullable=False)

    #code = Column(AqStr(16), nullable=False) #how to override the __init__?

    parent_id = Column(Integer, ForeignKey(
        'location.id', name='loc_parent_fk'), nullable=True)

    location_type = Column(AqStr(32), nullable=False)

    fullname = Column(String(255), nullable=False)

    creation_date = Column(DateTime, default=datetime.now, nullable=False)

    comments = Column(String(255), nullable=True)

    __mapper_args__ = {'polymorphic_on': location_type}

    def get_parents(self):
        pl = []
        p_node = self.parent
        if not p_node:
            return pl
        while p_node.parent is not None and p_node.parent != p_node:
            pl.append(p_node)
            p_node = p_node.parent
        pl.append(p_node)
        pl.reverse()
        return pl

    def get_p_dict(self):
        d = {}
        p_node = self
        while p_node.parent is not None and p_node.parent != p_node:
            d[str(p_node.location_type)] = p_node
            p_node = p_node.parent
        return d

    @property
    def parents(self):
        return self.get_parents()

    @property
    def p_dict(self):
        return self.get_p_dict()

    @property
    def hub(self):
        return self.p_dict.get('hub', None)

    @property
    def continent(self):
        return self.p_dict.get('continent', None)

    @property
    def country(self):
        return self.p_dict.get('country', None)

    @property
    def campus(self):
        return self.p_dict.get('campus', None)

    @property
    def city(self):
        return self.p_dict.get('city', None)

    @property
    def building(self):
        return self.p_dict.get('building', None)

    @property
    def room(self):
        return self.p_dict.get('room', None)

    @property
    def rack(self):
        return self.p_dict.get('rack', None)

    @property
    def chassis(self):
        return self.p_dict.get('chassis', None)

    @property
    def append(self, node):
        if isinstance(node, Location):
            node.parent = self
            self.sublocations[node] = node

    def offspring_ids(self, exclude_self=False):
        session = object_session(self)
        # We have two implementations here: the first is fast but
        # Oracle-specific, the second is slower but works with any database
        if session.connection().dialect.name == 'oracle':
            where = "WHERE id != %d" % self.id if exclude_self else ""
            s = text("""SELECT id FROM location
                        %s
                        CONNECT BY parent_id = PRIOR id
                        START WITH id = %d""" % (where, self.id))
            return s
        else:
            queue = deque([self.id])
            offsprings = []
            while queue:
                node_id = queue.popleft()
                offsprings.append(node_id)
                q = session.query(Location.id).filter_by(parent_id=node_id)
                children = [item.id for item in q.all()]
                queue.extend(children)
            if exclude_self:
                offsprings.remove(self.id)
            return offsprings

    def sysloc(self):
        components = ['building', 'city', 'continent']
        for component in components:
            if component not in self.p_dict:
                return None
        return str('.'.join([str(self.p_dict[item]) for item in components]))

    def get_parts(self):
        parts = list(self.parents)
        parts.append(self)
        return parts

    def merge(self, loc):
        """Find the common root of two locations."""
        # Optimization since get_parts can be expensive...
        if self == loc:
            return self
        merged = None
        for (self_part, loc_part) in zip(self.get_parts(), loc.get_parts()):
            if self_part != loc_part:
                return merged
            merged = self_part
        return merged

    def __repr__(self):
        return self.__class__.__name__ + " " + str(self.name)

    def __str__(self):
        return str(self.name)

location = Location.__table__

location.primary_key.name = 'location_pk'

location.append_constraint(
    UniqueConstraint('name', 'location_type', name='loc_name_type_uk'))

location.info['unique_fields'] = ['name', 'location_type']

Location.sublocations = relation('Location', backref=backref(
                                    'parent', remote_side=[location.c.id]))
