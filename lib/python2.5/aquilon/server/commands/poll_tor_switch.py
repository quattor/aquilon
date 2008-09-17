#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq poll tor_switch`."""


from csv import DictReader, Error as CSVError
from StringIO import StringIO

from twisted.python import log

from aquilon.exceptions_ import AquilonError, NotFoundException
from aquilon.server.broker import (add_transaction, az_check, format_results,
                                   BrokerCommand)
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

    @add_transaction
    @az_check
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
        if switch.ip:
            hostname = switch.ip
        elif switch.dns_domain.name == 'ms.com':
            hostname = switch.name
        else:
            hostname = switch.fqdn
        return run_command([self.config.get("broker", "CheckNet"),
                     "-ho", hostname, "camtable", "-nobanner",
                     "-table", "1", "-noprompt"])

    def parse_ports(self, results):
        macports = []
        try:
            reader = DictReader(StringIO(results))
            for row in reader:
                mac = row.get('fdbMacAddr', None)
                port = row.get('fdbSrcPort', None)
                if mac is None or port is None:
                    log.msg("Invalid line %d of CheckNet output." %
                            reader.line_num)
                    continue
                macports.append([mac, int(port)])
        except CSVError, e:
            raise AquilonError("Error parsing CheckNet results: %s" % e)
        return macports


#if __name__=='__main__':
