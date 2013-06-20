# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" How we represent location data in Aquilon """

from datetime import datetime
from sqlalchemy import (Integer, DateTime, Sequence, String, Column,
                        ForeignKey, UniqueConstraint, PrimaryKeyConstraint,
                        Index)

from sqlalchemy.orm import (relation, backref, object_session, deferred,
                            reconstructor)
from sqlalchemy.sql import and_, or_, desc

from aquilon.aqdb.model import Base, DnsDomain
from aquilon.aqdb.column_types import AqStr
from aquilon.exceptions_ import AquilonError


class Location(Base):
    """ How we represent location data in Aquilon """
    __tablename__ = 'location'

    valid_parents = []

    id = Column(Integer, Sequence('location_id_seq'), primary_key=True)

    name = Column(AqStr(16), nullable=False)

    location_type = Column(AqStr(32), nullable=False)

    fullname = Column(String(255), nullable=False)

    default_dns_domain_id = Column(Integer, ForeignKey('dns_domain.id',
                                                       name='location_dns_domain_fk',
                                                       ondelete='SET NULL'),
                                   nullable=True)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    comments = Column(String(255), nullable=True)

    default_dns_domain = relation(DnsDomain)

    __table_args__ = (UniqueConstraint(name, location_type,
                                       name='loc_name_type_uk'),)
    __mapper_args__ = {'polymorphic_on': location_type}

    def get_p_dict(self, loc_type):
        if self._parent_dict is None:
            self._parent_dict = {str(self.location_type): self}
            for node in self.parents:
                self._parent_dict[str(node.location_type)] = node
        return self._parent_dict.get(loc_type, None)

    @property
    def hub(self):
        return self.get_p_dict('hub')

    @property
    def continent(self):
        return self.get_p_dict('continent')

    @property
    def country(self):
        return self.get_p_dict('country')

    @property
    def campus(self):
        return self.get_p_dict('campus')

    @property
    def city(self):
        return self.get_p_dict('city')

    @property
    def building(self):
        return self.get_p_dict('building')

    @property
    def bunker(self):
        return self.get_p_dict('bunker')

    @property
    def room(self):
        return self.get_p_dict('room')

    @property
    def rack(self):
        return self.get_p_dict('rack')

    @property
    def chassis(self):
        return self.get_p_dict('chassis')

    def offspring_ids(self):
        session = object_session(self)
        q = session.query(Location.id)
        q = q.join((LocationLink, Location.id == LocationLink.child_id))
        # Include self as well
        q = q.filter(or_(Location.id == self.id,
                         LocationLink.parent_id == self.id))
        return q.subquery()

    def parent_ids(self):
        session = object_session(self)
        q = session.query(Location.id)
        q = q.join((LocationLink, Location.id == LocationLink.parent_id))
        # Include self as well
        q = q.filter(or_(Location.id == self.id,
                         LocationLink.child_id == self.id))
        return q.subquery()

    def sysloc(self):
        components = ('building', 'city', 'continent')
        names = []
        for component in components:
            value = self.get_p_dict(component)
            if not value:
                return None
            names.append(value.name)
        return str('.'.join(names))

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

    def __init__(self, parent=None, name=None, fullname=None, **kwargs):
        # Keep compatibility with the old behavior of the "parent" attribute
        # when creating new objects. Note that both the location manipulation
        # commands and the data loader in the unittest suite depends on this.
        if parent is not None:
            if parent.__class__ not in self.valid_parents:
                raise AquilonError("{0} cannot be a parent of {1:lc} {2}."
                                   .format(parent, self, name))
            session = object_session(parent)
            if not session:
                raise AquilonError("The parent must be persistent")

            # We have to disable autoflush in case parent._parent_links needs
            # loading, since self is not ready to be pushed to the DB yet
            with session.no_autoflush:
                for link in parent._parent_links:
                    session.add(LocationLink(child=self, parent=link.parent,
                                             distance=link.distance + 1))
                session.add(LocationLink(child=self, parent=parent, distance=1))
            session.expire(parent, ["_child_links", "children"])

        if not fullname:
            fullname = name

        super(Location, self).__init__(name=name, fullname=fullname, **kwargs)
        self._parent_dict = None

    @reconstructor
    def setup(self):
        self._parent_dict = None

    def update_parent(self, parent=None):
        session = object_session(self)
        if parent is None:  # pragma: no cover
            raise AquilonError("Parent location can be updated but not removed")
        if parent.__class__ not in self.valid_parents:
            raise AquilonError("{0} cannot be a parent of {1:l}."
                               .format(parent, self))

        # Disable autoflush. We'll make use of SQLA's ability to replace
        # DELETE + INSERT for the same LocationLink with an UPDATE of the
        # distance column.
        with session.no_autoflush:
            # Delete links to our old parent and its ancestors
            for plink in self._parent_links:
                q = session.query(LocationLink)
                q = q.filter(and_(LocationLink.child_id.in_(self.offspring_ids()),
                                  LocationLink.parent_id == plink.parent.id))
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
        self._parent_dict = None

location = Location.__table__  # pylint: disable=C0103
location.info['unique_fields'] = ['name', 'location_type']


class LocationLink(Base):
    __tablename__ = 'location_link'

    child_id = Column(Integer, ForeignKey('location.id',
                                          name='location_link_child_fk',
                                          ondelete='CASCADE'),
                      nullable=False)

    parent_id = Column(Integer, ForeignKey('location.id',
                                           name='location_link_parent_fk',
                                           ondelete='CASCADE'),
                       nullable=False)

    # Distance from the given parent. 1 means direct child.
    distance = Column(Integer, nullable=False)

    child = relation(Location, innerjoin=True, foreign_keys=child_id,
                     backref=backref("_parent_links",
                                     cascade="all, delete-orphan",
                                     passive_deletes=True))

    parent = relation(Location, innerjoin=True, foreign_keys=parent_id,
                      backref=backref("_child_links",
                                      cascade="all, delete-orphan",
                                      passive_deletes=True))

    __table_args__ = (PrimaryKeyConstraint(child_id, parent_id),
                      Index("location_link_parent_idx", parent_id))

# Make these relations view-only, to make sure the distance is managed
# explicitely
Location.parents = relation(Location,
                            secondary=LocationLink.__table__,
                            primaryjoin=Location.id == LocationLink.child_id,
                            secondaryjoin=Location.id == LocationLink.parent_id,
                            order_by=[desc(LocationLink.distance)],
                            viewonly=True,
                            backref=backref('children',
                                            order_by=[LocationLink.distance],
                                            viewonly=True))

# FIXME: this should be dropped when multiple parents are allowed
Location.parent = relation(Location, uselist=False,
                           secondary=LocationLink.__table__,
                           primaryjoin=and_(Location.id == LocationLink.child_id,
                                            LocationLink.distance == 1),
                           secondaryjoin=Location.id == LocationLink.parent_id,
                           viewonly=True)
