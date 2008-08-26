#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show location --type`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import NotFoundException
from aquilon.server.broker import (add_transaction, az_check, format_results,
                                   BrokerCommand)
from aquilon.aqdb.loc.location import Location


class CommandShowLocationType(BrokerCommand):

    required_parameters = ["type"]

    @add_transaction
    @az_check
    @format_results
    def render(self, session, type, name, **arguments):
        query = session.query(Location)
        if type:
            query = query.filter_by(location_type=type)
        if name:
            query = query.filter_by(name=name)
        if name and type:
            try:
                return query.one()
            except InvalidRequestError, e:
                raise NotFoundException(
                        "Location type='%s' name='%s' not found: %s"
                        % (type, name, e))
        return query.all()


#if __name__=='__main__':