# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show manager --manager`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.system import get_system
from aquilon.aqdb.model import Manager


class CommandShowManagerManager(BrokerCommand):

    required_parameters = ["manager"]

    def render(self, session, manager, **kwargs):
        return get_system(session, manager, Manager, 'Manager')


