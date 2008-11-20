#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains a wrapper for `aq show network --type`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.commands.show_network import CommandShowNetwork


class CommandShowNetworkType(CommandShowNetwork):
    """ CommandShowNetwork has all the necessary logic to
        handle the extra type parameter.

    """

    required_parameters = ["type"]


#if __name__=='__main__':
