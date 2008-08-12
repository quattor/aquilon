#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show location types`."""


from aquilon.server.broker import (add_transaction, az_check, format_results,
                                   BrokerCommand)


class CommandShowLocationTypes(BrokerCommand):

    @add_transaction
    @az_check
    @format_results
    def render(self, session, **arguments):
        return session.query(LocationType).all()


#if __name__=='__main__':
