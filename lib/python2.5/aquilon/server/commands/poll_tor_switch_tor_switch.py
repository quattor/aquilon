# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq poll tor_switch --tor_switch`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.commands.poll_tor_switch import CommandPollTorSwitch
from aquilon.server.dbwrappers.system import get_system
from aquilon.aqdb.sy.tor_switch import TorSwitch


class CommandPollTorSwitchTorSwitch(CommandPollTorSwitch):

    required_parameters = ["tor_switch"]

    def render(self, session, tor_switch, **arguments):
        dbtor_switch = get_system(session, tor_switch, TorSwitch, 'TorSwitch')
        return self.poll(session, [dbtor_switch])


