# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show host --all`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.formats.host import SimpleHostList
from aquilon.aqdb.model import Host


class CommandShowHostAll(BrokerCommand):

    def render(self, session, **arguments):
        return SimpleHostList(session.query(Host).all())


