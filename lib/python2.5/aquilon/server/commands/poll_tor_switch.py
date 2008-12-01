# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq poll tor_switch`."""


from csv import DictReader, Error as CSVError
from StringIO import StringIO

from twisted.python import log

from aquilon.exceptions_ import AquilonError, NotFoundException
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.observed_mac import get_or_create_observed_mac
from aquilon.server.processes import run_command
from aquilon.aqdb.sy.tor_switch import TorSwitch
from aquilon.aqdb.hw.hardware_entity import HardwareEntity


# This runs...
# CheckNet -ho np06bals03 camtable -nobanner -table 1 -noprompt
# ...which yields...
# Device_Name,fdbMacAddr,fdbVlan,fdbVlanId,fdbSrcPort,fdbSrcTrunk,fdbState,fdbRefSps,fdbLearnedPort,fbStatus
#np06bals03,003048663a62,103,103,17,0,forward,,0,notpermanent
#np06bals03,001f29c439ba,103,103,2,0,forward,,0,notpermanent
#np06bals03,0030486638e6,103,103,22,0,forward,,0,notpermanent
#np06bals03,001f29c429ca,103,103,4,0,forward,,0,notpermanent
# ...and the mac/port combos are added to the switch info.

class CommandPollTorSwitch(BrokerCommand):
    """ The CheckNet command seems to run fine without a module load.
        Leaving it like that for now.  In the future, we may need a

        module load /ms/dist/NetEng/modules/prod

    """

    required_parameters = ["rack"]

    def render(self, session, rack, **arguments):
        dblocation = get_location(session, rack=rack)
        q = session.query(TorSwitch)
        #q = q.join('tor_switch_hw')
        #q = q.filter_by(location=dblocation)
        q = q.filter(TorSwitch.tor_switch_id==HardwareEntity.id)
        q = q.filter(HardwareEntity.location_id==dblocation.id)
        switches = q.all()
        if not switches:
            raise NotFoundException("No switch found.")
        return self.poll(session, switches)

    def poll(self, session, switches):
        for switch in switches:
            out = self.run_checknet(switch)
            macports = self.parse_ports(out)
            for (mac, port) in macports:
                get_or_create_observed_mac(session, switch, port, mac)
        return

    def run_checknet(self, switch):
        if switch.dns_domain.name == 'ms.com':
            hostname = switch.name
        else:
            hostname = switch.fqdn
        return run_command([self.config.get("broker", "CheckNet"),
                     "-ho", hostname, "camtable", "-nobanner",
                     "-table", "1", "-noprompt"])

    def parse_ports(self, results):
        """ This method could require switch and have hard-coded field
            names based on the switch model, but for now just loosely
            searches for any known fields."""
        macports = []
        try:
            reader = DictReader(StringIO(results))
            mac_label = None
            port_label = None
            for row in reader:
                if not mac_label:
                    if 'fdbMacAddr' in reader.fieldnames:
                        # BNT
                        mac_label = 'fdbMacAddr'
                    elif 'Mac' in reader.fieldnames:
                        # Cisco
                        mac_label = 'Mac'
                    else:
                        raise AquilonError("Invalid CheckNet header, no field for mac address." % e)
                if not port_label:
                    if 'fdbSrcPort' in reader.fieldnames:
                        # BNT
                        port_label = 'fdbSrcPort'
                    elif 'dot1dTpFdbPort' in reader.fieldnames:
                        # Cisco
                        port_label = 'dot1dTpFdbPort'
                    else:
                        raise AquilonError("Invalid CheckNet header, no field for source port." % e)
                mac = row.get(mac_label, None)
                port = row.get(port_label, None)
                if mac is None or port is None:
                    log.msg("Invalid line %d of CheckNet output." %
                            reader.line_num)
                    continue
                macports.append([mac, int(port)])
        except CSVError, e:
            raise AquilonError("Error parsing CheckNet results: %s" % e)
        return macports


