#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show host --hostname`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.host import hostname_to_host


class CommandShowHostHostname(BrokerCommand):

    required_parameters = ["hostname"]

    def render(self, session, hostname, **kwargs):
        return hostname_to_host(session, hostname)


#if __name__=='__main__':
