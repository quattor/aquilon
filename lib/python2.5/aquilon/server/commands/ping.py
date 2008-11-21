# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq ping`."""


from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)


class CommandPing(BrokerCommand):

    @format_results
    def render(self, **arguments):
        return "pong"


