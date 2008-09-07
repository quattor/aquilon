#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
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
from aquilon.server.dbwrappers.system import parse_system_and_verify_free
from aquilon.aqdb.sy.tor_switch import TorSwitch
from aquilon.aqdb.hw.tor_switch_hw import TorSwitchHw
from aquilon.aqdb.hw.switch_port import SwitchPort
from aquilon.aqdb.hw.interface import Interface
from aquilon.aqdb.hw.hardware_entity import HardwareEntity
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

        (short, dbdns_domain) = parse_system_and_verify_free(session,
                                                             tor_switch)

        dbtor_switch_hw = TorSwitchHw(location=dblocation, model=dbmodel,
                                      serial_no=serial)
        session.save(dbtor_switch_hw)
        dbtor_switch = TorSwitch(name=short, dns_domain=dbdns_domain,
                                 tor_switch_hw=dbtor_switch_hw)

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
            dbnetwork = get_net_id_from_ip(session, ip)
            # Hmm... should this check apply to the switch's own network?
            restrict_tor_offsets(session, dbnetwork, ip)
            dbtor_switch.mac = mac
            dbtor_switch.ip = ip
            dbtor_switch.network = dbnetwork
            session.update(dbtor_switch)
            dbinterface = Interface(name=interface, interface_type='public',
                                    mac=mac, system=dbtor_switch,
                                    hardware_entity=dbtor_switch_hw)
            session.save(dbinterface)
            session.flush()

            # FIXME: This information will need to go to dsdb.
        return


#if __name__=='__main__':
