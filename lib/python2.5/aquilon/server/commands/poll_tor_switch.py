# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Contains the logic for `aq poll tor_switch`."""


from csv import DictReader, Error as CSVError
from StringIO import StringIO

from aquilon.exceptions_ import AquilonError, NotFoundException
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.observed_mac import get_or_create_observed_mac
from aquilon.server.processes import run_command
from aquilon.aqdb.model import TorSwitch, HardwareEntity


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

    def render(self, session, logger, rack, **arguments):
        dblocation = get_location(session, rack=rack)
        q = session.query(TorSwitch)
        #q = q.join('tor_switch_hw')
        #q = q.filter_by(location=dblocation)
        q = q.filter(TorSwitch.tor_switch_id==HardwareEntity.id)
        q = q.filter(HardwareEntity.location_id==dblocation.id)
        switches = q.all()
        if not switches:
            raise NotFoundException("No switch found.")
        return self.poll(session, logger, switches)

    def poll(self, session, logger, switches):
        for switch in switches:
            out = self.run_checknet(logger, switch)
            macports = self.parse_ports(logger, out)
            for (mac, port) in macports:
                get_or_create_observed_mac(session, switch, port, mac)
        return

    def run_checknet(self, logger, switch):
        if switch.dns_domain.name == 'ms.com':
            hostname = switch.name
        else:
            hostname = switch.fqdn
        return run_command([self.config.get("broker", "CheckNet"),
                            "-ho", hostname, "camtable", "-nobanner",
                            "-table", "1", "-noprompt"],
                           logger=logger)

    def parse_ports(self, logger, results):
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
                if mac is None or port is None or \
                   len(mac) == 0 or len(port) == 0:
                    logger.info("Missing value for mac or port in CheckNet "
                                "output line #%d: %s" % (reader.line_num, row))
                    continue
                try:
                    port_int = int(port)
                except ValueError, e:
                    logger.info("Error parsing port number in CheckNet output "
                                "line #%d: %s error: %s" %
                                (reader.line_num, row, e))
                    continue
                macports.append([mac, port_int])

        except CSVError, e:
            raise AquilonError("Error parsing CheckNet results: %s" % e)
        return macports
