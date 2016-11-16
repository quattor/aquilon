# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2016 Contributor
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

""" Tables/classes for configuration based on building pairs. """

from datetime import datetime
from operator import attrgetter

from sqlalchemy import (DateTime, Column, ForeignKey, PrimaryKeyConstraint,
                        CheckConstraint)
from sqlalchemy.orm import column_property, deferred, relation, validates
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import and_, or_, case, exists
from sqlalchemy.util import KeyedTuple

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.aqdb.model import Base, Building, Archetype
from aquilon.aqdb.model.base import _raise_custom

_TN = 'building_preference'


class BuildingPreference(Base):
    """ Table identifying for particular building pairs which building
        should be preferred by default. """
    __tablename__ = _TN
    _class_label = 'Building Preference'

    a_id = Column(ForeignKey(Building.id, name="%s_bldg_a_fk" % _TN,
                             ondelete='CASCADE'),
                  nullable=False)

    b_id = Column(ForeignKey(Building.id, name="%s_bldg_b_fk" % _TN,
                             ondelete='CASCADE'),
                  nullable=False, index=True)

    archetype_id = Column(ForeignKey(Archetype.id, ondelete="CASCADE"),
                          nullable=False, index=True)

    prefer_id = Column(ForeignKey(Building.id, name="%s_prefer_fk" % _TN),
                       nullable=False, index=True)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    a = relation(Building, foreign_keys=a_id, innerjoin=True)
    b = relation(Building, foreign_keys=b_id, innerjoin=True)
    prefer = relation(Building, foreign_keys=prefer_id, innerjoin=True)
    archetype = relation(Archetype, innerjoin=True)

    __table_args__ = (PrimaryKeyConstraint(a_id, b_id, archetype_id),
                      CheckConstraint(and_(a_id < b_id,
                                           or_(a_id == prefer_id,
                                               b_id == prefer_id))),
                      {'info': {'unique_fields': ['a', 'b', 'archetype']}})

    def __init__(self, a, b, archetype, prefer):
        super(BuildingPreference, self).__init__(a=a, b=b, archetype=archetype)
        # Trigger the validator only after a and b has been set
        self.prefer = prefer

    @validates('prefer')
    def validate_prefer(self, key, value):  # pylint: disable=W0613
        if value != self.a and value != self.b:
            raise ArgumentError("Preferred {2:l} must be one of "
                                "{0.name} and {1.name}."
                                .format(self.a, self.b, value))
        return value

    @property
    def sorted_name(self):
        # The pair is sorted by ID in the DB to allow enforcing uniqueness, but
        # for display purposes, sorting by name makes more sense
        return ",".join(sorted([self.a.name, self.b.name]))

    @property
    def qualified_name(self):
        return self.sorted_name + "," + self.archetype.name

    @classmethod
    def parse_pair(cls, session, building_pair):
        """
        Parse a comma-separated building pair.

        The pair is returned in the order expected by the database, which
        currently means sorted by Building.id.
        """
        pair = [Building.get_unique(session, item, compel=True)
                for item in building_pair.split(",")]
        if len(pair) != 2:
            raise ArgumentError("Building pair %s should be two building "
                                "codes separated by a comma." % building_pair)

        if pair[0] == pair[1]:
            raise ArgumentError("Building pair should consist of two different "
                                "building codes.")

        pair.sort(key=attrgetter('id'))
        return KeyedTuple(pair, labels=("a", "b"))

    @classmethod
    def ordered_pair(cls, buildings):
        assert len(buildings) == 2

        pair = sorted(buildings, key=attrgetter('id'))
        return KeyedTuple(pair, labels=("a", "b"))

    @classmethod
    def get_unique(cls, session, a=None, b=None, building_pair=None,
                   archetype=None, compel=False, preclude=False):
        # pylint: disable=W0221
        assert archetype is not None
        if not isinstance(archetype, Archetype):
            archetype = Archetype.get_unique(session, archetype, compel=True)

        # The caller should specify either both a and b, or building_pair
        if building_pair:
            assert a is None
            assert b is None

            # Allow passing the output of parse_pair() as argument
            if not isinstance(building_pair, KeyedTuple):
                building_pair = cls.parse_pair(session, building_pair)
            a = building_pair.a
            b = building_pair.b
        else:
            # We could accept strings and call Building.get_unique() ourselves,
            # but there's no use case yet
            assert isinstance(a, Building)
            assert isinstance(b, Building)

        q = session.query(cls)
        q = q.filter_by(a=a, b=b, archetype=archetype)
        try:
            result = q.one()
            if preclude:
                msg = "Building pair {0.sorted_name} already has a preference for {1:l}."
                msg = msg.format(result, result.archetype)
                _raise_custom(preclude, ArgumentError, msg)
        except NoResultFound:
            if not compel:
                return None
            pair_name = ",".join(sorted([a.name, b.name]))
            msg = "Building pair {0} does not have a preference for {1:l}."
            msg = msg.format(pair_name, archetype)
            _raise_custom(compel, NotFoundException, msg)

        return result

# This property can be pre-loaded to speed up checking if there are any building
# preferences set for a given archetype. The CASE may look redundant, but Oracle
# does not understand "SELECT EXISTS (...) AS ...", so this trick is needed to
# convert EXISTS to a proper column expression.
Archetype.has_building_preferences = column_property(
    case([(exists([1])
           .where(Archetype.id == BuildingPreference.archetype_id), True)],
         else_=False), deferred=True)
