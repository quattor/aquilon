#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show chassis --name`."""


from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.system import get_system


class CommandShowChassisName(BrokerCommand):

    required_parameters = ["name"]

    @add_transaction
    @az_check
    @format_results
    def render(self, session, name, **arguments):
        # FIXME: Constrain this to be Chassis?
        return get_system(session, name)


#if __name__=='__main__':
