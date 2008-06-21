#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show model`."""


from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.aqdb.hardware import Model, Vendor, MachineType


class CommandShowModel(BrokerCommand):
    """ This is more like a 'search' command than a 'show' command, and
        will probably be converted at some time in the future."""

    @add_transaction
    @az_check
    @format_results
    def render(self, session, name, vendor, type, **arguments):
        q = session.query(Model)
        if name is not None:
            q = q.filter(Model.name.like(name + '%'))
        if vendor is not None:
            q = q.join('vendor').filter(Vendor.name.like(vendor + '%'))
            q = q.reset_joinpoint()
        if type is not None:
            q = q.join('machine_type').filter(MachineType.type.like(type + '%'))
            q = q.reset_joinpoint()
        return q.all()


#if __name__=='__main__':
