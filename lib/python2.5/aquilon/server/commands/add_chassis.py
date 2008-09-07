#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add chassis`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.aqdb.sy.chassis import Chassis
from aquilon.aqdb.hw.chassis_hw import ChassisHw
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.model import get_model
from aquilon.server.dbwrappers.system import parse_system_and_verify_free


class CommandAddChassis(BrokerCommand):

    required_parameters = ["name", "rack", "model"]

    @add_transaction
    @az_check
    def render(self, session, name, rack, serial, model, comments, **arguments):
        (short, dbdns_domain) = parse_system_and_verify_free(session, name)
        dblocation = get_location(session, rack=rack)
        dbmodel = get_model(session, model)
        if dbmodel.machine_type not in ['chassis']:
            raise ArgumentError("Model must be of type chassis.")
        # FIXME: Precreate chassis slots?
        dbchassis_hw = ChassisHw(location=dblocation, model=dbmodel,
                                 serial_no=serial)
        session.save(dbchassis_hw)
        dbchassis = Chassis(name=short, dns_domain=dbdns_domain,
                            chassis_hw=dbchassis_hw, comments=comments)
        session.save(dbchassis)
        return


#if __name__=='__main__':
