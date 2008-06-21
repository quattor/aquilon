#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq del location`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import NotFoundException
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.aqdb.location import Location


class CommandDelLocation(BrokerCommand):

    required_parameters = ["name", "type"]

    @add_transaction
    @az_check
    def render(self, session, name, type, **arguments):
        try:
            dblocation = session.query(Location).filter_by(name=name
                    ).join('type').filter_by(type=type).one()
        except InvalidRequestError, e:
            raise NotFoundException(
                    "Location type='%s' name='%s' not found: %s"
                    % (type, name, e))
        session.delete(dblocation)
        return


#if __name__=='__main__':
