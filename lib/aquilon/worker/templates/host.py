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
"""Any work by the broker to write out (or read in?) templates lives here."""


import logging
from operator import attrgetter
from collections import defaultdict

from aquilon.config import Config
from aquilon.exceptions_ import IncompleteError, InternalError
from aquilon.aqdb.model import (Host, VlanInterface, BondingInterface,
                                BridgeInterface)
from aquilon.worker.locks import CompileKey
from aquilon.worker.templates.base import Plenary, PlenaryCollection
from aquilon.worker.templates.cluster import PlenaryClusterClient
from aquilon.worker.templates.panutils import (StructureTemplate, PanValue,
                                               pan_assign, pan_append,
                                               pan_include)

LOGGER = logging.getLogger(__name__)


def select_routers(dbmachine, routers):
    filtered = []

    # Networks stretched between two buildings may have two routers, one in each
    # building. If a host wants to talk to some other host in the same building,
    # but uses the router in the remote building, then the data travels between
    # the buildings twice. To avoid this case, we filter out routers that are
    # not in the same building where the host is.
    #
    # If the routers are not inside a building, then we assume that either the
    # network is not stretched or this problem is dealt with using some other
    # mechanism (e.g. VRRP), and we consider the routers as equal.
    dbbuilding = dbmachine.location and dbmachine.location.building or None
    for router in routers:
        if not router.location or not router.location.building or \
           router.location.building == dbbuilding:
            filtered.append(router.ip)

    # If the location information is wrong, we still want to have a router.
    # Pick one since we have no better information.
    if not filtered and routers:
        filtered.append(routers[0].ip)
    return filtered


def is_default_route(dbinterface):
    """ Check if the given interface should provide the default route

    The default route should point to a given interface if:
    - it is the boot interface
    - it is a bonding/bridge and one of the members is the boot interface
    """
    if dbinterface.default_route:
        return True
    for slave in dbinterface.slaves:
        if is_default_route(slave):
            return True
    return False


class PlenaryHost(PlenaryCollection):
    """
    A facade for Toplevel and Namespaced Hosts (below).

    This class creates either/both toplevel and namespaced host plenaries,
    based on broker configuration:
    namespaced_host_profiles (boolean):
      if namespaced profiles should be generated
    flat_host_profiles (boolean):
      if host profiles should be put into a "flat" toplevel (non-namespaced)
    """
    def __init__(self, dbhost, logger=LOGGER):
        if not isinstance(dbhost, Host):
            raise InternalError("PlenaryHost called with %s instead of Host" %
                                dbhost.__class__.name)
        PlenaryCollection.__init__(self, logger=logger)
        self.dbobj = dbhost
        self.config = Config()
        if self.config.getboolean("broker", "namespaced_host_profiles"):
            self.plenaries.append(PlenaryNamespacedHost(dbhost))
        if self.config.getboolean("broker", "flat_host_profiles"):
            self.plenaries.append(PlenaryToplevelHost(dbhost))
        self.plenaries.append(PlenaryHostData(dbhost))

    def write(self, locked=False, content=None):
        # Don't bother writing plenary files non-compilable archetypes.
        if not self.dbobj.archetype.is_compileable:
            return 0

        # Standard PlenaryCollection swallows IncompleteError.  If/when
        # the Host plenaries no longer raise that error this override
        # should be removed.
        total = 0
        for plenary in self.plenaries:
            total += plenary.write(locked=locked, content=content)
        return total


Plenary.handlers[Host] = PlenaryHost


class PlenaryHostData(Plenary):

    template_type = "structure"

    def __init__(self, dbhost, logger=LOGGER):
        Plenary.__init__(self, dbhost, logger=logger)
        # Store the branch separately so get_key() works even after the dbhost
        # object has been deleted
        self.branch = dbhost.branch
        self.name = dbhost.fqdn
        self.plenary_core = "hostdata"
        self.plenary_template = self.name

    def get_key(self):
        # Going with self.name instead of self.plenary_template_name seems like
        # the right decision here - easier to predict behavior when meshing
        # with other CompileKey generators like PlenaryMachine.
        return CompileKey(domain=self.branch.name, profile=self.name,
                          logger=self.logger)

    def body(self, lines):
        interfaces = dict()
        routers = {}
        default_gateway = None

        pers = self.dbobj.personality

        # FIXME: Enforce that one of the interfaces is marked boot?
        for dbinterface in self.dbobj.machine.interfaces:
            # Management interfaces are not configured at the host level
            if dbinterface.interface_type == 'management':
                continue

            ifdesc = {}

            if dbinterface.master:
                ifdesc["bootproto"] = "none"
                if isinstance(dbinterface.master, BondingInterface):
                    ifdesc["master"] = dbinterface.master.name
                elif isinstance(dbinterface.master, BridgeInterface):
                    ifdesc["bridge"] = dbinterface.master.name
                else:
                    raise InternalError("Unexpected master interface type: "
                                        "{0}".format(dbinterface.master))
            else:
                if dbinterface.assignments:
                    # TODO: Let the templates select from "static"/"dhcp"
                    ifdesc["bootproto"] = "static"
                else:
                    # Don't try to bring up the interface if there are no
                    # addresses assigned to it
                    ifdesc["bootproto"] = "none"

            if isinstance(dbinterface, VlanInterface):
                ifdesc["vlan"] = True
                ifdesc["physdev"] = dbinterface.parent.name

            static_routes = set()

            for addr in dbinterface.assignments:
                # Service addresses will be handled as resources
                if addr.service_address:
                    continue

                net = addr.network

                if addr.label == "":
                    if net.routers:
                        local_rtrs = select_routers(self.dbobj.machine,
                                                    net.routers)
                        gateway = local_rtrs[0]
                        if is_default_route(dbinterface):
                            routers[dbinterface.name] = local_rtrs
                    else:
                        # No routers defided, fall back to the default
                        gateway = net.network[net.default_gateway_offset]

                    # TODO: generate appropriate routing policy if there are
                    # multiple interfaces marked as default_route
                    if not default_gateway and is_default_route(dbinterface):
                        default_gateway = gateway

                    ifdesc["ip"] = addr.ip
                    ifdesc["netmask"] = net.netmask
                    ifdesc["broadcast"] = net.broadcast
                    ifdesc["gateway"] = gateway
                    ifdesc["network_type"] = net.network_type
                    ifdesc["network_environment"] = net.network_environment.name
                    if addr.dns_records:
                        ifdesc["fqdn"] = addr.dns_records[0]
                else:
                    aliasdesc = {"ip": addr.ip,
                                 "netmask": net.netmask,
                                 "broadcast": net.broadcast}
                    if addr.dns_records:
                        aliasdesc["fqdn"] = addr.dns_records[0]
                    if "aliases" in ifdesc:
                        ifdesc["aliases"][addr.label] = aliasdesc
                    else:
                        ifdesc["aliases"] = {addr.label: aliasdesc}

                static_routes |= set(net.static_routes)

            if static_routes:
                if "route" not in ifdesc:
                    ifdesc["route"] = []
                # Enforce a stable order to make it easier to verify changes in
                # the plenaries
                for route in sorted(list(static_routes),
                                    key=attrgetter('destination', 'gateway_ip')):
                    ifdesc["route"].append({"address": route.destination.ip,
                                            "netmask": route.destination.netmask,
                                            "gateway": route.gateway_ip})
                if not ifdesc["route"]:
                    del ifdesc["route"]

            interfaces[dbinterface.name] = ifdesc

        # Okay, here's the real content
        pmachine = Plenary.get_plenary(self.dbobj.machine, logger=self.logger)
        pan_assign(lines, "hardware",
                   StructureTemplate(pmachine.plenary_template_name))

        lines.append("")
        pan_assign(lines, "system/network/interfaces", interfaces)
        pan_assign(lines, "system/network/primary_ip",
                   self.dbobj.machine.primary_ip)
        if default_gateway:
            pan_assign(lines, "system/network/default_gateway",
                       default_gateway)
        if routers:
            pan_assign(lines, "system/network/routers", routers)
        lines.append("")

        pan_assign(lines, "system/build", self.dbobj.status.name)
        pan_assign(lines, "system/advertise_status", self.dbobj.advertise_status)

        ## process grns
        eon_id_map = defaultdict(set)

        # own
        for grn_rec in self.dbobj._grns:
            eon_id_map[grn_rec.target].add(grn_rec.grn.eon_id)

        # pers level
        for grn_rec in pers._grns:
            eon_id_map[grn_rec.target].add(grn_rec.grn.eon_id)

        for (target, eon_id_set) in eon_id_map.iteritems():
            eon_id_list = list(eon_id_set)
            eon_id_list.sort()
            pan_assign(lines, "system/eon_id_maps/%s" % target, eon_id_list)

        # backward compat for esp reporting
        archetype = self.dbobj.archetype.name
        if self.config.has_option("archetype_" + archetype,
                                  "default_grn_target"):
            default_grn_target = self.config.get("archetype_" + archetype,
                                                 "default_grn_target")

            eon_id_set = eon_id_map[default_grn_target]

            eon_id_list = list(eon_id_set)
            eon_id_list.sort()
            if eon_id_list:
                pan_assign(lines, "system/eon_ids", eon_id_list)

        pan_assign(lines, "system/owner_eon_id", self.dbobj.owner_eon_id)

        if self.dbobj.cluster:
            pan_assign(lines, "system/cluster/name", self.dbobj.cluster.name)
            pan_assign(lines, "system/cluster/node_index",
                       self.dbobj._cluster.node_index)
        if self.dbobj.resholder:
            lines.append("")
            for resource in sorted(self.dbobj.resholder.resources,
                                   key=attrgetter('resource_type', 'name')):
                pan_append(lines, "system/resources/" + resource.resource_type,
                           StructureTemplate(resource.template_base +
                                             '/config'))


class PlenaryToplevelHost(Plenary):
    """
    A plenary template for a host, stored at the toplevel of the profiledir
    """

    template_type = "object"

    def __init__(self, dbhost, logger=LOGGER):
        Plenary.__init__(self, dbhost, logger=logger)
        # Store the branch separately so get_key() works even after the dbhost
        # object has been deleted
        self.branch = dbhost.branch
        self.name = dbhost.fqdn
        self.loadpath = dbhost.personality.archetype.name
        self.plenary_core = ""
        self.plenary_template = self.name

    def will_change(self):
        # Need to override to handle IncompleteError...
        self.stash()
        if not self.new_content:
            try:
                self.new_content = self._generate_content()
            except IncompleteError:
                # Attempting to have IncompleteError thrown later by
                # not caching the return
                return self.old_content is None
        return self.old_content != self.new_content

    def get_key(self):
        # Going with self.name instead of self.plenary_template_name seems like
        # the right decision here - easier to predict behavior when meshing
        # with other CompileKey generators like PlenaryMachine.
        return CompileKey(domain=self.branch.name, profile=self.name,
                          logger=self.logger)

    def body(self, lines):
        pers = self.dbobj.personality
        arch = pers.archetype

        # FIXME: Enforce that one of the interfaces is marked boot?
        for dbinterface in self.dbobj.machine.interfaces:
            # Management interfaces are not configured at the host level
            if dbinterface.interface_type == 'management':
                continue

        services = []
        required_services = set(arch.services + pers.services)

        for si in self.dbobj.services_used:
            required_services.discard(si.service)
            services.append(si.cfg_path + '/client/config')
        if required_services:
            missing = ", ".join(sorted([srv.name for srv in required_services]))
            raise IncompleteError("Host %s is missing the following required "
                                  "services, please run 'aq reconfigure': %s." %
                                  (self.name, missing))

        provides = []
        for si in self.dbobj.services_provided:
            provides.append('%s/server/config' % si.cfg_path)

        # Ensure used/provided services have a stable order
        services.sort()
        provides.sort()

        # Okay, here's the real content
        pan_include(lines, ["pan/units", "pan/functions"])
        lines.append("")

        pan_assign(lines, "/",
                   StructureTemplate("hostdata/%s" % self.name,
                                     {"metadata": PanValue("/metadata")}))
        pan_include(lines, "archetype/base")
        pan_include(lines, self.dbobj.operating_system.cfg_path + '/config')

        pan_include(lines, services)
        pan_include(lines, provides)

        personality_template = "personality/%s/config" % \
            self.dbobj.personality.name

        pan_include(lines, personality_template)

        if self.dbobj.cluster:
            clplenary = PlenaryClusterClient(self.dbobj.cluster)
            pan_include(lines, clplenary.plenary_template_name)
        elif pers.cluster_required:
            raise IncompleteError("Host %s personality %s requires cluster "
                                  "membership, please run 'aq cluster'." %
                                  (self.name, pers.name))
        pan_include(lines, "archetype/final")


class PlenaryNamespacedHost(PlenaryToplevelHost):
    """
    A plenary template describing a host, namespaced by DNS domain
    """
    def __init__(self, dbhost, logger=LOGGER):
        PlenaryToplevelHost.__init__(self, dbhost, logger=logger)
        self.plenary_core = dbhost.fqdn.dns_domain.name
