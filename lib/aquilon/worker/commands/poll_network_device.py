# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018  Contributor
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
"""Contains the logic for `aq poll network_device`."""

from csv import DictReader, Error as CSVError
from json import JSONDecoder
from datetime import datetime

from six.moves import cStringIO as StringIO  # pylint: disable=F0401

from aquilon.exceptions_ import (AquilonError, ArgumentError, NotFoundException,
                                 ProcessException, UnimplementedError)
from aquilon.utils import force_ip, validate_json
from aquilon.aqdb.types import MACAddress
from aquilon.aqdb.model import (NetworkDevice, ObservedMac, PortGroup, Network,
                                NetworkEnvironment, VlanInfo, Rack)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.observed_mac import (
    update_or_create_observed_mac)
from aquilon.worker.dbwrappers.network_device import (determine_helper_hostname,
                                                      determine_helper_args)
from aquilon.worker.locks import ExternalKey
from aquilon.worker.processes import run_command


class CommandPollNetworkDevice(BrokerCommand):

    required_parameters = ["rack"]

    def render(self, session, logger, rack, type, clear, vlan, **_):
        if vlan:
            raise UnimplementedError("vlan argument is no longer available")
        dblocation = Rack.get_unique(session, rack, compel=True)
        NetworkDevice.check_type(type)
        q = session.query(NetworkDevice)
        q = q.filter_by(location=dblocation)
        if type:
            q = q.filter_by(switch_type=type)
        netdevs = q.all()
        if not netdevs:
            raise NotFoundException("No network device found.")
        return self.poll(session, logger, netdevs, clear, vlan)

    def poll(self, session, logger, netdevs, clear, vlan):
        now = datetime.now()
        default_ssh_args = determine_helper_args(self.config)
        for netdev in netdevs:
            if clear:
                self.clear(session, netdev)

            hostname = determine_helper_hostname(session, logger, self.config,
                                                 netdev)
            if hostname:
                ssh_args = default_ssh_args[:]
                ssh_args.append(hostname)
            else:
                ssh_args = []

            with ExternalKey("poll_network_device", [netdev], logger=logger):
                self.poll_mac(session, netdev, now, ssh_args)
        return

    def poll_mac(self, session, netdev, now, ssh_args):
        importer = self.config.lookup_tool("get-camtable")

        if not netdev.primary_name:
            hostname = netdev.label
        elif netdev.primary_name.fqdn.dns_domain.name == 'ms.com':
            hostname = netdev.primary_name.fqdn.name
        else:
            hostname = netdev.fqdn
        args = []

        if ssh_args:
            args.extend(ssh_args)
        # TODO debug options shows CheckNet fails to return data and not
        # get-camtable
        args.extend([importer, "--debug", hostname])

        try:
            out = run_command(args)
        except ProcessException as err:
            raise ArgumentError("Failed to run network device discovery: %s" % err)

        macports = JSONDecoder().decode(out)
        validate_json(self.config, macports, "discovered_macs",
                      "discovered MACs")
        for (mac, port) in macports:
            update_or_create_observed_mac(session, netdev, port,
                                          MACAddress(mac), now)

    def clear(self, session, netdev):
        session.query(ObservedMac).filter_by(network_device=netdev).delete()
        session.flush()

