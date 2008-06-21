#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrapper to make getting a location simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon import const
from aquilon.exceptions_ import NotFoundException, ArgumentError
from aquilon.aqdb.location import Location


def get_location(session, **kwargs):
    """Somewhat sophisticated getter for any of the location types."""
    location_type = None
    for lt in const.location_types:
        if kwargs.get(lt):
            if location_type:
                raise ArgumentError("Single location can not be both %s and %s"
                        % (lt, location_type))
            location_type = lt
    if not location_type:
        return None
    try:
        dblocation = session.query(Location).filter_by(
                name=kwargs[location_type]).join('type').filter_by(
                type=location_type).one()
    except InvalidRequestError, e:
        raise NotFoundException("%s '%s' not found: %s"
                % (location_type.capitalize(), kwargs[location_type], e))
    return dblocation


#if __name__=='__main__':
