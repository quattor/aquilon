#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show tor_switch`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import (add_transaction, az_check, format_results,
                                   BrokerCommand)
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.model import get_model
from aquilon.server.dbwrappers.system import parse_system
from aquilon.aqdb.sy.tor_switch import TorSwitch
from aquilon.aqdb.hw.hardware_entity import HardwareEntity


class CommandShowTorSwitch(BrokerCommand):

    @add_transaction
    @az_check
    @format_results
    def render(self, session, tor_switch, rack, model, **arguments):
        q = session.query(TorSwitch)
        if tor_switch:
            (short, dbdns_domain) = parse_system(session, tor_switch)
            q = q.filter_by(name=short, dns_domain=dbdns_domain)
        if rack:
            dblocation = get_location(session, rack=rack)
            q = q.filter(TorSwitch.tor_switch_id==HardwareEntity.id)
            q = q.filter(HardwareEntity.location_id==dblocation.id)
        if model:
            dbmodel = get_model(session, model)
            if dbmodel.machine_type not in ['tor_switch']:
                raise ArgumentError(
                        "Requested model %s is a %s, not a tor_switch." %
                        (model, dbmodel.machine_type))
            q = q.filter(TorSwitch.tor_switch_id==HardwareEntity.id)
            q = q.filter(HardwareEntity.model_id==dbmodel.id)
        return q.all()


#if __name__=='__main__':
