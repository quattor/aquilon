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
"""Contains the logic for `aq add location`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import Location

# FIXME: This probably belongs in location.py
# It's also broken, as campus is not strictly between country and city.
# The list of imports above needs to include all of these entries.
location_types = ("company", "hub", "continent", "country", "campus",
                  "city", "building", "room", "rack", "desk")


def add_location(session, name, fullname, type, parent_name, parent_type,
                 comments=None, address=None):
    """ Perform all the initialization and error checking to add a location

        Returns a new location which has not been added to any session, allows
        code reuse while also being able to run DSDB commands before commiting
        the transactions
    """

    for value in [type, parent_type]:
        if value not in Location.__mapper__.polymorphic_map:
            raise ArgumentError("%s is not a known location type." %
                                value.capitalize())

    Location.get_unique(session, name=name, location_type=type, preclude=True)

    parent = Location.get_unique(session, name=parent_name,
                                 location_type=parent_type, compel=True)

    type_weight = location_types.index(type)
    parent_weight = location_types.index(parent_type)

    if type_weight <= parent_weight:
        raise ArgumentError("Type %s cannot be a parent of %s." %
                    (parent_type.capitalize(), type.capitalize()))

    location_type = Location.__mapper__.polymorphic_map[type].class_

    if not fullname:
        fullname = name

    kw = {'name': name, 'fullname': fullname, 'parent': parent,
          'comments': comments}

    if type == 'building':
        kw['address'] = address

    return location_type(**kw)


class CommandAddLocation(BrokerCommand):

    required_parameters = ["name", "fullname", "type", "parentname",
                           "parenttype"]

    def render(self, session, name, fullname, type, parentname, parenttype,
               comments=None, address=None, **arguments):

        new_loc = add_location(session, name, fullname, type, parentname,
                                 parenttype, comments, address)

        self.before_flush(session, new_loc, **arguments)

        session.add(new_loc)
        session.flush()

        self.after_flush(session, new_loc, **arguments)

        return

    def before_flush(self, session, new_loc, **arguments):
        "preparing steps for CommandAddLocation subclasses"
        pass

    def after_flush(self, session, new_loc, **arguments):
        "post operations steps for CommandAddLocation subclasses"
        pass
