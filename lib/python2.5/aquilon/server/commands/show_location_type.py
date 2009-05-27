# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show location --type`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import NotFoundException
from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.model import Location


class CommandShowLocationType(BrokerCommand):

    required_parameters = ["type"]

    def render(self, session, type, name, **arguments):
        query = session.query(Location)
        query = query.with_polymorphic(
            Location.__mapper__.polymorphic_map.values())
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


