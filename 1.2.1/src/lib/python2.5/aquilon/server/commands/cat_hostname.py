#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq cat --hostname`."""


from aquilon.server.broker import (add_transaction, az_check, format_results,
                                   BrokerCommand)
from aquilon.server.dbwrappers.host import hostname_to_host
from aquilon.server.processes import read_file


class CommandCatHostname(BrokerCommand):

    required_parameters = ["hostname"]

    @add_transaction
    @az_check
    #@format_results
    def render(self, session, hostname, **kwargs):
        dbhost = hostname_to_host(session, hostname)

        return read_file(self.config.get("broker", "hostsdir"),
                hostname + '.tpl')

#if __name__=='__main__':
