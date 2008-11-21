# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains a wrapper for `aq add manager --manager`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.commands.add_manager import CommandAddManager


class CommandAddManagerManager(CommandAddManager):
    """ CommandAddManager already has all the necessary logic to
        handle the extra instance parameter.

    """

    required_parameters = ["manager", "hostname"]


