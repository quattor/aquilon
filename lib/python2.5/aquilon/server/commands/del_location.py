# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq del location`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import NotFoundException
from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.model import Location


class CommandDelLocation(BrokerCommand):

    required_parameters = ["name", "type"]

    def render(self, session, name, type, **arguments):
        try:
            dblocation = session.query(Location).filter_by(name=name,
                    location_type=type).one()
        except InvalidRequestError, e:
            raise NotFoundException(
                    "Location type='%s' name='%s' not found: %s"
                    % (type, name, e))
        session.delete(dblocation)
        return


