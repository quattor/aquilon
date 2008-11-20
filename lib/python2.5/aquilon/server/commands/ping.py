#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq ping`."""


from aquilon.server.broker import BrokerCommand


class CommandPing(BrokerCommand):

    requires_transaction = False
    requires_azcheck = False
    requires_format = True

    def render(self, **arguments):
        return "pong"


#if __name__=='__main__':
