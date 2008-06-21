#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add location`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon import const
from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.aqdb.location import Location, LocationType, Company, Hub, \
        Continent, Country, City, Building, Rack, Chassis, Desk


# FIXME: This probably belongs in location.py
const.location_types = ("company", "hub", "continent", "country", "city",
        "building", "rack", "chassis", "desk")


class CommandAddLocation(BrokerCommand):

    required_parameters = ["name", "fullname", "type",
            "parentname", "parenttype", "comments"]

    @add_transaction
    @az_check
    def render(self, session, name, fullname, type, 
            parentname, parenttype, comments, **arguments):
        newLocation = session.query(Location).filter_by(name=name
                ).join('type').filter_by(type=type).first()
        if newLocation:
            # FIXME: Technically this is coming in with an http PUT,
            # which should try to adjust state and succeed if everything
            # is alright.
            raise ArgumentError("%s '%s' already exists."
                    % (type.capitalize(), name))
        try:
            parent = session.query(Location).filter_by(name=parentname
                    ).join('type').filter_by(type=parenttype).one()
        except InvalidRequestError:
            raise ArgumentError(
                    "Parent %s %s not found."
                    % (parenttype.capitalize(), parentname))
        # Incoming looks like 'city', need the City class.
        location_type = globals()[type.capitalize()]
        if not issubclass(location_type, Location):
            raise ArgumentError("%s is not a known location type" % type)
        try:
            dblt = session.query(LocationType).filter_by(type=type).one()
        except InvalidRequestError:
            raise ArgumentError("Invalid location type '%s'" % type)

        # Figure out if it is valid to add this type of child to the parent...
        found_parent = False
        found_new = False
        for t in const.location_types:
            if t == parenttype:
                # Great, found the parent type in the list before requested type
                found_parent = True
                continue
            if t != type:
                # This item is neither parent nor new, keep going...
                continue
            # Moment of truth.
            if found_parent:
                # We saw the parent earlier - life is good.
                found_new = True
                break
            raise ArgumentError("type %s cannot be a parent of %s" %
                    (parenttype, type))
        if not found_new:
            raise ArgumentError("unknown type %s" % type)

        optional_args = {}
        if fullname:
            optional_args["fullname"] = fullname
        if comments:
            optional_args["comments"] = comments

        newLocation = location_type(name=name, type_name=dblt,
                parent=parent, **optional_args)
        return


#if __name__=='__main__':
