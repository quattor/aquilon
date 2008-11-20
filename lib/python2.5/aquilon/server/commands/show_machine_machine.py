#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show machine --machine`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.commands.show_machine import CommandShowMachine


class CommandShowMachineMachine(CommandShowMachine):
    """The base class already has the necessary logic to handle this."""

    required_parameters = ["machine"]


#if __name__=='__main__':
