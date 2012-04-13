# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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
from sqlalchemy import (Integer, DateTime, Sequence, String, Column,
                        ForeignKey, UniqueConstraint)

from sqlalchemy.orm import relation, backref, object_session, deferred
from sqlalchemy.sql import and_, or_, desc

from aquilon.aqdb.model import Base
from aquilon.aqdb.column_types import AqStr
from aquilon.exceptions_ import AquilonError

class Location(Base):
    """ How we represent location data in Aquilon """
    __tablename__ = 'location'

    id = Column(Integer, Sequence('location_id_seq'), primary_key=True)

    name = Column(AqStr(16), nullable=False)

    location_type = Column(AqStr(32), nullable=False)

    fullname = Column(String(255), nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    comments = Column(String(255), nullable=True)

    __mapper_args__ = {'polymorphic_on': location_type}

    def get_p_dict(self):
        d = {str(self.location_type): self}
        for p_node in self.parents:
            d[str(p_node.location_type)] = p_node
        return d

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

    def offspring_ids(self):
        session = object_session(self)
        q = session.query(Location.id)
        q = q.join((LocationLink, Location.id == LocationLink.child_id))
        # Include self as well
        q = q.filter(or_(Location.id == self.id,
                         LocationLink.parent_id == self.id))
        return q.subquery()

    def sysloc(self):
        components = ['building', 'city', 'continent']
        for component in components:
            if component not in self.p_dict:
                return None
        return str('.'.join([self.p_dict[item].name for item in components]))

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

    def __init__(self, parent=None, **kwargs):
        # Keep compatibility with the old behavior of the "parent" attribute
        # when creating new objects. Note that both the location manipulation
        # commands and the data loader in the unittest suite depends on this.
        if parent is not None:
            session = object_session(parent)
            if not session:
                raise AquilonError("The parent must be persistent")

            # We have to disable autoflush in case parent._parent_links needs
            # loading, since self is not ready to be pushed to the DB yet
            flush_state = session.autoflush
            session.autoflush = False
            for link in parent._parent_links:
                session.add(LocationLink(child=self, parent=link.parent,
                                         distance=link.distance + 1))
            session.add(LocationLink(child=self, parent=parent, distance=1))
            session.expire(parent, ["_child_links", "children"])
            session.autoflush = flush_state

        super(Location, self).__init__(**kwargs)

    def update_parent(self, parent=None):
        session = object_session(self)
        if parent is None:  # pragma: no cover
            raise AquilonError("Parent location can be updated but not removed")

        # Disable autoflush. We'll make use of SQLA's ability to replace
        # DELETE + INSERT for the same LocationLink with an UPDATE of the
        # distance column.
        flush_state = session.autoflush
        session.autoflush = False

        # Delete links to our old parent and its ancestors
        for plink in self._parent_links:
            q = session.query(LocationLink)
            q = q.filter(and_(LocationLink.child_id.in_(self.offspring_ids()),
                              LocationLink.parent_id==plink.parent.id))
            # See above: we depend on the caching ability of the session, so
            # we can't use q.delete()
            for clink in q.all():
                session.delete(clink)

        # Add links to the new parent
        session.add(LocationLink(child=self, parent=parent, distance=1))
        for clink in self._child_links:
            session.add(LocationLink(child_id=clink.child_id,
                                     parent=parent,
                                     distance=clink.distance + 1))

        # Add links to the new parent's ancestors
        for plink in parent._parent_links:
            session.add(LocationLink(child=self, parent_id=plink.parent_id,
                                     distance=plink.distance + 1))
            for clink in self._child_links:
                session.add(LocationLink(child_id=clink.child_id,
                                         parent_id=plink.parent_id,
                                         distance=plink.distance +
                                         clink.distance + 1))

        session.flush()
        session.expire(parent, ["_child_links", "children"])
        session.expire(self, ["_parent_links", "parent", "parents"])

        session.autoflush = flush_state


location = Location.__table__  # pylint: disable-msg=C0103, E1101

location.primary_key.name = 'location_pk'
location.info['unique_fields'] = ['name', 'location_type']

location.append_constraint(
    UniqueConstraint('name', 'location_type', name='loc_name_type_uk'))


class LocationLink(Base):
    __tablename__ = 'location_link'

    child_id = Column(Integer, ForeignKey('location.id',
                                          name='location_link_child_fk',
                                          ondelete='CASCADE'),
                      primary_key=True)

    parent_id = Column(Integer, ForeignKey('location.id',
                                           name='location_link_parent_fk',
                                           ondelete='CASCADE'),
                       primary_key=True)

    # Distance from the given parent. 1 means direct child.
    distance = Column(Integer, nullable=False)

    child = relation(Location, innerjoin=True,
                     primaryjoin=child_id == Location.id,
                     backref=backref("_parent_links",
                                     cascade="all, delete-orphan",
                                     passive_deletes=True))

    parent = relation(Location, innerjoin=True,
                      primaryjoin=parent_id == Location.id,
                      backref=backref("_child_links",
                                      cascade="all, delete-orphan",
                                      passive_deletes=True))


llink = LocationLink.__table__  # pylint: disable=C0103, E1101
llink.primary_key.name = 'location_link_pk'

# Make these relations view-only, to make sure
# the distance is managed explicitely
Location.parents = relation(Location,
                            secondary=LocationLink.__table__,
                            primaryjoin=Location.id == LocationLink.child_id,
                            secondaryjoin=Location.id == LocationLink.parent_id,
                            order_by=[desc(LocationLink.distance)],
                            viewonly=True)

# FIXME: this should be dropped when multiple parents are allowed
Location.parent = relation(Location, uselist=False,
                           secondary=LocationLink.__table__,
                           primaryjoin=and_(Location.id == LocationLink.child_id,
                                            LocationLink.distance == 1),
                           secondaryjoin=Location.id == LocationLink.parent_id,
                           viewonly=True)

Location.children = relation(Location,
                             secondary=LocationLink.__table__,
                             primaryjoin=Location.id == LocationLink.parent_id,
                             secondaryjoin=Location.id == LocationLink.child_id,
                             order_by=[LocationLink.distance],
                             viewonly=True)
