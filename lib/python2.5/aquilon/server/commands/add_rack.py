#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add rack`."""


from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.rack import get_or_create_rack


class CommandAddRack(BrokerCommand):

    required_parameters = ["rackid", "building", "row", "column"]

    @add_transaction
    @az_check
    def render(self, session, rackid, building, row, column, fullname,
            comments, **arguments):
        dbrack = get_or_create_rack(session=session, rackid=rackid,
                building=building, rackrow=row, rackcolumn=column,
                fullname=fullname, comments=comments)
        return


#if __name__=='__main__':
