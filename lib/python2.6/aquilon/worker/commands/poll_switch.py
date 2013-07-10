# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Contains the logic for `aq poll switch`."""


from csv import DictReader, Error as CSVError
from json import JSONDecoder
from StringIO import StringIO
from datetime import datetime

from aquilon.exceptions_ import (AquilonError, ArgumentError, InternalError,
                                 NotFoundException, ProcessException)
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.dbwrappers.observed_mac import (
    update_or_create_observed_mac)
from aquilon.worker.dbwrappers.switch import (determine_helper_hostname,
                                              determine_helper_args)
from aquilon.worker.processes import run_command
from aquilon.aqdb.model import (Switch, ObservedMac, ObservedVlan, Network,
                                NetworkEnvironment, VlanInfo)
from aquilon.utils import force_ipv4


class CommandPollSwitch(BrokerCommand):

    required_parameters = ["rack"]

    def render(self, session, logger, rack, type, clear, vlan, **arguments):
        dblocation = get_location(session, rack=rack)
        Switch.check_type(type)
        q = session.query(Switch)
        q = q.filter_by(location=dblocation)
        if type:
            q = q.filter_by(switch_type=type)
        switches = q.all()
        if not switches:
            raise NotFoundException("No switch found.")
        return self.poll(session, logger, switches, clear, vlan)

    def poll(self, session, logger, switches, clear, vlan):
        now = datetime.now()
        failed_vlan = 0
        default_ssh_args = determine_helper_args(self.config)
        for switch in switches:
            if clear:
                self.clear(session, switch)

            hostname = determine_helper_hostname(session, logger, self.config,
                                                 switch)
            if hostname:
                ssh_args = default_ssh_args[:]
                ssh_args.append(hostname)
            else:
                ssh_args = []

            self.poll_mac(session, switch, now, ssh_args)
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

    def poll_mac(self, session, switch, now, ssh_args):
        importer = self.config.get("broker", "get_camtable")

        if not switch.primary_name:
            hostname = switch.label
        elif switch.primary_name.fqdn.dns_domain.name == 'ms.com':
            hostname = switch.primary_name.fqdn.name
        else:
            hostname = switch.fqdn
        args = []

        if ssh_args:
            args.extend(ssh_args)
        # TODO debug options shows CheckNet fails to return data and not
        # get-camtable
        args.extend([importer, "--debug", hostname])

        try:
            out = run_command(args)
        except ProcessException, err:
            raise ArgumentError("Failed to run switch discovery: %s" % err)

        macports = JSONDecoder().decode(out)
        for (mac, port) in macports:
            update_or_create_observed_mac(session, switch, port, mac, now)

    def clear(self, session, switch):
        session.query(ObservedMac).filter_by(switch=switch).delete()
        session.flush()

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

                vlan_info = VlanInfo.get_unique(session, vlan_id=vlan_int,
                                                compel=False)
                if not vlan_info:
                    logger.client_info("vlan {0} is not defined in AQ. Please "
                            "use add_vlan to add it.".format(vlan_int))
                    continue

                if vlan_info.vlan_type == "unknown":
                    continue

                dbvlan = ObservedVlan(vlan_id=vlan_int, switch=switch,
                                      network=dbnetwork, creation_date=now)
                session.add(dbvlan)
        except CSVError, e:
            raise AquilonError("Error parsing vlan2net results: %s" % e)
