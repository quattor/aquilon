#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq search hardware`."""


from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.formats.hardware_entity import SimpleHardwareEntityList
from aquilon.aqdb.hw.hardware_entity import HardwareEntity
from aquilon.server.dbwrappers.hardware_entity import (
    search_hardware_entity_query)


class CommandSearchHardware(BrokerCommand):

    required_parameters = []

    @add_transaction
    @az_check
    @format_results
    def render(self, session, fullinfo, **arguments):
        q = search_hardware_entity_query(session, HardwareEntity, **arguments)
        if fullinfo:
            return q.all()
        return SimpleHardwareEntityList(q.all())


#if __name__=='__main__':
