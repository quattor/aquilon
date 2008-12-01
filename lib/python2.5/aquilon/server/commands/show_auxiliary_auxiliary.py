# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show auxiliary --auxiliary`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.system import get_system
from aquilon.aqdb.sy.auxiliary import Auxiliary


class CommandShowAuxiliaryAuxiliary(BrokerCommand):

    required_parameters = ["auxiliary"]

    def render(self, session, auxiliary, **kwargs):
        return get_system(session, auxiliary, Auxiliary, 'Auxiliary')


