# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show model`."""


from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.model import Model, Vendor


class CommandShowModel(BrokerCommand):
    """ This is more like a 'search' command than a 'show' command, and
        will probably be converted at some time in the future."""

    def render(self, session, name, vendor, type, **arguments):
        q = session.query(Model)
        if name is not None:
            q = q.filter(Model.name.like(name + '%'))
        if vendor is not None:
            q = q.join('vendor').filter(Vendor.name.like(vendor + '%'))
            q = q.reset_joinpoint()
        if type is not None:
            q = q.filter(Model.machine_type.like(type + '%'))
        return q.all()
