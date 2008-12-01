# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show tor_switch --tor_switch`."""


from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.commands.show_tor_switch import CommandShowTorSwitch


class CommandShowTorSwitchTorSwitch(CommandShowTorSwitch):
    """The base class already has the necessary logic to handle this."""

    required_parameters = ["tor_switch"]


