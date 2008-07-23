#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add tor_switch`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.model import get_model
from aquilon.server.dbwrappers.machine import create_machine
from aquilon.aqdb.hw.switch_port import SwitchPort
from aquilon.aqdb.hw.physical_interface import PhysicalInterface
from aquilon.aqdb.loc.rack import Rack


class CommandAddTorSwitch(BrokerCommand):

    required_parameters = ["tor_switch", "model"]

    @add_transaction
    @az_check
    def render(self, session,
            tor_switch, model,
            rack, building, rackid,
            interface, mac, ip,
            cpuname, cpuvendor, cpuspeed, cpucount, memory,
            serial,
            user, **arguments):
        dbmodel = get_model(session, model)

        if dbmodel.machine_type not in ['tor_switch']:
            raise ArgumentError("The add_tor_switch command cannot add machines of type '%s'.  Try 'add machine'." %
                    dbmodel.machine_type)

        if rack:
            dblocation = get_location(session, rack=rack)
        elif building and rackid is not None:
            dbbuilding = get_location(session, building=building)
            # Because of http, rackid comes in as a string.  It just
            # gets treated as such here.
            # Check for redundancy...
            if len(rackid) > len(dbbuilding.name) and rackid.startswith(
                    dbbuilding.name):
                rack = rackid
            else:
                rack = dbbuilding.name + rackid
            dblocation = session.query(Rack).filter_by(name=rack).first()
            if not dblocation:
                dblocation = Rack(name=rack, fullname=rack, parent=dbbuilding,
                        comments="Created for tor_switch %s" % tor_switch)
                session.save(dblocation)
        else:
            raise ArgumentError("Need to specify either --building and --rackid or --rack")

        dbtor_switch = create_machine(session, tor_switch, dblocation, dbmodel,
            cpuname, cpuvendor, cpuspeed, cpucount, memory, serial)

        # FIXME: Hard-coded number of switch ports...
        switch_port_start = 1
        switch_port_count = 48
        switch_port_end = switch_port_start + switch_port_count
        for i in range(switch_port_start, switch_port_end):
            dbsp = SwitchPort(switch=dbtor_switch, port_number=i)
            session.save(dbsp)

        if interface or mac or ip:
            if not (interface and mac and ip):
                raise ArgumentError("If using --interface, --mac, or --ip, all of them must be given.")
            dbpi = PhysicalInterface(name=interface, mac=mac, ip=ip,
                    machine=dbtor_switch)
            session.save(dbpi)
            session.flush()
            session.refresh(dbpi)

            # FIXME: This information may need to go to dsdb.

        session.refresh(dbtor_switch)

        return


#if __name__=='__main__':
