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
from aquilon.server.dbwrappers.rack import get_or_create_rack
from aquilon.server.dbwrappers.interface import restrict_tor_offsets
from aquilon.server.dbwrappers.ip_address import get_or_create_ip_address
from aquilon.server.dbwrappers.a_name import get_or_create_a_name
from aquilon.server.dbwrappers.mac_address import (
        create_or_get_free_mac_address)
from aquilon.aqdb.hw.tor_switch import TorSwitch
from aquilon.aqdb.hw.switch_port import SwitchPort
from aquilon.aqdb.hw.interface import Interface
from aquilon.aqdb.loc.rack import Rack
from aquilon.aqdb.net.ip_to_int import get_net_id_from_ip


class CommandAddTorSwitch(BrokerCommand):

    required_parameters = ["tor_switch", "model"]

    @add_transaction
    @az_check
    def render(self, session,
            tor_switch, model,
            rack, building, rackid, rackrow, rackcolumn,
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
        elif (building and rackid is not None and
                rackrow and rackcolumn is not None):
            dblocation = get_or_create_rack(session, rackid=rackid,
                    building=building, rackrow=rackrow, rackcolumn=rackcolumn,
                    comments="Created for tor_switch %s" % tor_switch)
        else:
            raise ArgumentError("Need to specify an existing --rack or provide --building, --rackid, --rackrow and --rackcolumn")

        dba_name = get_or_create_a_name(session, tor_switch)
        if session.query(HardwareEntity).filter_by(name=dba_name).first():
            raise ArgumentError("The name '%s' is already in use." %
                                tor_switch)

        dbtor_switch = TorSwitch(name=dba_name, location=dblocation,
                                 model=dbmodel, serial_no=serial)

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
            dbmac = create_or_get_free_mac_address(session, mac)
            # FIXME: Need to associate this IP with the interface
            dbip = get_or_create_ip_address(session, ip)
            dbnetwork = get_net_id_from_ip(session, ip)
            # Hmm... should this check apply to the switch's own network?
            restrict_tor_offsets(session, dbnetwork, ip)
            dbinterface = Interface(name=interface,
                                    hardware_entity=dbtor_switch)
            session.save(dbinterface)
            dbmac.interface = dbinterface
            session.update(dbmac)
            session.flush()

            # FIXME: This information will need to go to dsdb.
        return


#if __name__=='__main__':
