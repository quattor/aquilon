# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq del disk --disk`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.commands.del_disk import CommandDelDisk


class CommandDelDiskDisk(CommandDelDisk):
    """The base class already has the necessary logic to handle this."""

    required_parameters = ["machine", "disk"]


