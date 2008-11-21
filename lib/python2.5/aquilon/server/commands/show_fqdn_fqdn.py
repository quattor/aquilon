# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show fqdn --fqdn`."""


from aquilon.server.broker import (add_transaction, az_check, format_results,
                                   BrokerCommand)
from aquilon.server.dbwrappers.system import get_system


class CommandShowFqdnFqdn(BrokerCommand):

    required_parameters = ["fqdn"]

    @add_transaction
    @az_check
    @format_results
    def render(self, session, fqdn, **kwargs):
        return get_system(session, fqdn)


