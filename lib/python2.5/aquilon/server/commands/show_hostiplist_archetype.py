# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains a wrapper for `aq show hostiplist --archetype`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.commands.show_hostiplist import CommandShowHostIPList


class CommandShowHostIPListArchetype(CommandShowHostIPList):
    """ CommandShowHostIPList already has all the necessary logic to
        handle the extra archetype parameter.

    """

    required_parameters = ["archetype"]


