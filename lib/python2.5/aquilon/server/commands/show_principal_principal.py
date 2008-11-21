# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show principal --principal`."""


from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.user_principal import (
        get_or_create_user_principal)


class CommandShowPrincipal(BrokerCommand):

    required_parameters = ["principal"]

    @add_transaction
    @az_check
    @format_results
    def render(self, session, principal, **arguments):
        try:
            return get_or_create_user_principal(
                    session, principal, False, False)
        except ArgumentError, e:
            raise NotFoundException("UserPrincipal %s not found" % principal)


