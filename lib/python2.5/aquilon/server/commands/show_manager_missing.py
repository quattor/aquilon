# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show manager --missing`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.formats.interface import MissingManagersList
from aquilon.aqdb.hw.interface import Interface


class CommandShowManagerMissing(BrokerCommand):

    def render(self, session, **arguments):
        q = session.query(Interface)
        q = q.filter_by(interface_type='management')
        q = q.filter(Interface.system==None)
        q = q.join('hardware_entity')
        q = q.filter_by(hardware_entity_type='machine')
        return MissingManagersList(q.all())


