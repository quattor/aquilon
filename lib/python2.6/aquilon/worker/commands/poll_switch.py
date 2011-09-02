# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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
"""Contains the logic for `aq poll switch`."""


from csv import DictReader, Error as CSVError
from StringIO import StringIO
from datetime import datetime
from random import choice

from aquilon.exceptions_ import (AquilonError, ArgumentError, InternalError,
                                 NotFoundException, ProcessException)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.dbwrappers.observed_mac import (
    update_or_create_observed_mac)
from aquilon.worker.processes import run_command
from aquilon.aqdb.model import (Switch, ObservedMac, ObservedVlan, Network,
                                NetworkEnvironment, Service, ServiceInstance)
from aquilon.utils import force_ipv4


# This runs...
# CheckNet -ho np06bals03 camtable -nobanner -table 1 -noprompt
# ...which yields...
# Device_Name,fdbMacAddr,fdbVlan,fdbVlanId,fdbSrcPort,fdbSrcTrunk,fdbState,fdbRefSps,fdbLearnedPort,fbStatus
#np06bals03,003048663a62,103,103,17,0,forward,,0,notpermanent
#np06bals03,001f29c439ba,103,103,2,0,forward,,0,notpermanent
#np06bals03,0030486638e6,103,103,22,0,forward,,0,notpermanent
#np06bals03,001f29c429ca,103,103,4,0,forward,,0,notpermanent
# ...and the mac/port combos are added to the switch info.

class CommandPollSwitch(BrokerCommand):
    """ The CheckNet command seems to run fine without a module load.
        Leaving it like that for now.  In the future, we may need a

        module load /ms/dist/NetEng/modules/prod

    """

    required_parameters = ["rack"]

    def render(self, session, logger, rack, clear, vlan, **arguments):
        dblocation = get_location(session, rack=rack)
        q = session.query(Switch)
        q = q.filter(Switch.location_id==dblocation.id)
        switches = q.all()
        if not switches:
            raise NotFoundException("No switch found.")
        return self.poll(session, logger, switches, clear, vlan)

    def poll(self, session, logger, switches, clear, vlan):
        now = datetime.now()
        failed_vlan = 0
        default_ssh_args = self.determine_helper_args()
        for switch in switches:
            if clear:
                self.clear(session, logger, switch)

            hostname = self.determine_helper_hostname(session, logger, switch)
            if hostname:
                ssh_args = default_ssh_args[:]
                ssh_args.append(hostname)
            else:
                ssh_args = []

            self.poll_mac(session, logger, switch, now, ssh_args)
            if vlan:
                if switch.switch_type != "tor":
                    logger.client_info("Skipping VLAN probing on {0:l}, it's "
                                       "not a ToR switch.".format(switch))
                    continue

                try:
                    self.poll_vlan(session, logger, switch, now, ssh_args)
                except ProcessException, e:
                    failed_vlan += 1
                    logger.client_info("Failed getting VLAN info for {0:l}: "
                                       "{1!s}".format(switch, e))
        if switches and failed_vlan == len(switches):
            raise ArgumentError("Failed getting VLAN info.")
        return

    def determine_helper_args(self):
        ssh_command = self.config.get("broker", "poll_ssh").strip()
        if not ssh_command:  # pragma: no cover
            return []
        ssh_args = [ssh_command]
        ssh_options = self.config.get("broker", "poll_ssh_options")
        ssh_args.extend(ssh_options.strip().split())
        return ssh_args

    def determine_helper_hostname(self, session, logger, switch):
        """Try to figure out a useful helper from the mappings.
        """
        helper_name = self.config.get("broker", "poll_helper_service")
        if not helper_name:  # pragma: no cover
            return
        helper_service = Service.get_unique(session, helper_name,
                                            compel=InternalError)
        # TODO: eventually we should use the Chooser here
        for loc in switch.location.parents:
            q = session.query(ServiceInstance)
            q = q.filter_by(service=helper_service)
            q = q.join(['service_map'])
            q = q.filter_by(location=loc)
            dbsi = q.first()
            if dbsi and dbsi.server_hosts:
                # Poor man's load balancing...
                jump = choice(dbsi.server_hosts).fqdn
                logger.client_info("Using jump host {0} from {1:l}, mapped to "
                                   "{2:l} to run CheckNet for {3:l}.".format(
                                       jump, dbsi, loc, switch))
                return jump

        logger.client_info("No jump host for %s, calling CheckNet from %s." %
                           (switch, self.config.get("broker", "hostname")))
        return None

    def poll_mac(self, session, logger, switch, now, ssh_args):
        out = self.run_checknet(logger, switch, ssh_args)
        macports = self.parse_ports(logger, out)
        for (mac, port) in macports:
            update_or_create_observed_mac(session, switch, port, mac, now)

    def clear(self, session, logger, switch):
        session.query(ObservedMac).filter_by(switch=switch).delete()
        session.flush()

    def run_checknet(self, logger, switch, ssh_args):
        if not switch.primary_name:
            hostname = switch.label
        elif switch.primary_name.fqdn.dns_domain.name == 'ms.com':
            hostname = switch.primary_name.fqdn.name
        else:
            hostname = switch.fqdn
        args = []
        if ssh_args:
            args.extend(ssh_args)
        args.extend([self.config.get("broker", "CheckNet"), "-ho", hostname,
                     "camtable", "-nobanner", "-table", "1", "-noprompt"])
        return run_command(args, logger=logger)

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
                        raise AquilonError("Invalid CheckNet header, no field "
                                           "for MAC address.")
                if not port_label:
                    if 'fdbSrcPort' in reader.fieldnames:
                        # BNT
                        port_label = 'fdbSrcPort'
                    elif 'dot1dTpFdbPort' in reader.fieldnames:
                        # Cisco
                        port_label = 'dot1dTpFdbPort'
                    else:
                        raise AquilonError("Invalid CheckNet header, no field "
                                           "for source port.")
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

    def poll_vlan(self, session, logger, switch, now, ssh_args):
        if not switch.primary_ip:
            raise ArgumentError("Cannot poll VLAN info for {0:l} without "
                                "a registered IP address.".format(switch))
        session.query(ObservedVlan).filter_by(switch=switch).delete()
        session.flush()

        # Restrict operations to the internal network
        dbnet_env = NetworkEnvironment.get_unique_or_default(session)

        args = []
        if ssh_args:
            args.extend(ssh_args)
        args.append(self.config.get("broker", "vlan2net"))
        args.append("-ip")
        args.append(switch.primary_ip)
        out = run_command(args)

        try:
            reader = DictReader(StringIO(out))
            for row in reader:
                vlan = row.get("vlan", None)
                network = row.get("network", None)
                bitmask = row.get("bitmask", None)
                if vlan is None or network is None or bitmask is None or \
                   len(vlan) == 0 or len(network) == 0 or len(bitmask) == 0:
                    logger.info("Missing value for vlan, network or bitmask in "
                                "output line #%d: %s" % (reader.line_num, row))
                    continue
                try:
                    vlan_int = int(vlan)
                except ValueError, e:
                    logger.info("Error parsing vlan number in output "
                                "line #%d: %s error: %s" %
                                (reader.line_num, row, e))
                    continue
                try:
                    network = force_ipv4("network", network)
                except ArgumentError, e:
                    raise InternalError(e)
                try:
                    bitmask_int = int(bitmask)
                except ValueError, e:
                    logger.info("Error parsing bitmask in output "
                                "line #%d: %s error: %s" %
                                (reader.line_num, row, e))
                    continue
                dbnetwork = Network.get_unique(session, ip=network,
                                               network_environment=dbnet_env)
                if not dbnetwork:
                    logger.info("Unknown network %s in output line #%d: %s" %
                                (network, reader.line_num, row))
                    continue
                if dbnetwork.cidr != bitmask_int:
                    logger.client_info("{0}: skipping VLAN {1}, because network "
                                       "bitmask value {2} differs from prefixlen "
                                       "{3.cidr} of {3:l}.".format(switch, vlan,
                                                                   bitmask,
                                                                   dbnetwork))
                    continue
                dbvlan = ObservedVlan(vlan_id=vlan_int, switch=switch,
                                      network=dbnetwork, creation_date=now)
                session.add(dbvlan)
        except CSVError, e:
            raise AquilonError("Error parsing vlan2net results: %s" % e)
