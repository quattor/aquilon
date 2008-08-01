#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains a wrapper for `aq add windows host`."""


from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.commands.add_host import CommandAddHost


class CommandAddWindowsHost(CommandAddHost):

    required_parameters = ["hostname", "machine", "status"]

    @add_transaction
    @az_check
    def render(self, *args, **kwargs):
        kwargs['archetype'] = 'windows'
        kwargs['domain'] = 'windows_domain'
        # The superclass already contains the logic to handle this case.
        return CommandAddHost.render(self, *args, **kwargs)


#if __name__=='__main__':
