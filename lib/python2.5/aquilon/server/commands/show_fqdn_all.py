# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show fqdn --all`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.formats.system import SimpleSystemList
from aquilon.aqdb.model import System


class CommandShowFqdnAll(BrokerCommand):

    def render(self, session, **arguments):
        return SimpleSystemList(session.query(System).all())


