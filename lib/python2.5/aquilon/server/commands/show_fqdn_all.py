#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show fqdn --all`."""


from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.formats.system import SimpleSystemList
from aquilon.aqdb.sy.system import System


class CommandShowFqdnAll(BrokerCommand):

    @add_transaction
    @az_check
    @format_results
    def render(self, session, **arguments):
        return SimpleSystemList(session.query(System).all())


#if __name__=='__main__':
