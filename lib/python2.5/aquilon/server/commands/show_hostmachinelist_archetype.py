#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains a wrapper for `aq show hostmachinelist --archetype`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.commands.show_hostmachinelist import CommandShowHostMachineList


class CommandShowHostMachineListArchetype(CommandShowHostMachineList):
    """ CommandShowHostMachineList already has all the necessary logic to
        handle the extra archetype parameter.

    """

    required_parameters = ["archetype"]


#if __name__=='__main__':
