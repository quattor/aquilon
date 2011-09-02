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
"""Any work by the broker to write out (or read in?) templates lives here."""


import logging

from aquilon.config import Config
from aquilon.exceptions_ import IncompleteError, InternalError, ArgumentError
from aquilon.aqdb.model import (Host, VlanInterface, BondingInterface,
                                BridgeInterface)
from aquilon.worker.locks import CompileKey
from aquilon.worker.templates.base import Plenary, PlenaryCollection
from aquilon.worker.templates.machine import PlenaryMachineInfo
from aquilon.worker.templates.cluster import PlenaryClusterClient
from aquilon.worker.templates.panutils import pan, StructureTemplate
from aquilon.worker.dbwrappers.feature import (model_features,
                                               personality_features,
                                               interface_features)

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
        self.config = Config()
        if self.config.getboolean("broker", "namespaced_host_profiles"):
            self.plenaries.append(PlenaryNamespacedHost(dbhost, logger=logger))
        if self.config.getboolean("broker", "flat_host_profiles"):
            self.plenaries.append(PlenaryToplevelHost(dbhost, logger=logger))

    def write(self, dir=None, locked=False, content=None):
        # Standard PlenaryCollection swallows IncompleteError.  If/when
        # the Host plenaries no longer raise that error this override
        # should be removed.
        total = 0
        for plenary in self.plenaries:
            total += plenary.write(dir=dir, locked=locked, content=content)
        return total


class PlenaryToplevelHost(Plenary):
    """
    A plenary template for a host, stored at the toplevel of the profiledir
    """
    def __init__(self, dbhost, logger=LOGGER):
        Plenary.__init__(self, dbhost, logger=logger)
        self.dbhost = dbhost
        # Store the branch separately so get_key() works even after the dbhost
        # object has been deleted
        self.branch = dbhost.branch.name
        self.name = dbhost.fqdn
        self.plenary_core = ""
        self.plenary_template = "%(name)s" % self.__dict__
        self.template_type = "object"
        self.dir = "%s/domains/%s/profiles" % (
            self.config.get("broker", "builddir"), self.branch)

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
        # Going with self.name instead of self.plenary_template seems like
        # the right decision here - easier to predict behavior when meshing
        # with other CompileKey generators like PlenaryMachine.
        return CompileKey(domain=self.branch, profile=self.name,
                          logger=self.logger)

    def body(self, lines):
        interfaces = dict()
        vips = dict()
        transit_interfaces = []
        routers = {}
        default_gateway = None
        iface_features = {}

        pers = self.dbhost.personality
        arch = pers.archetype

        # FIXME: Enforce that one of the interfaces is marked boot?
        for dbinterface in self.dbhost.machine.interfaces:
            # Management interfaces are not configured at the host level
            if dbinterface.interface_type == 'management':
                continue

            featlist = interface_features(dbinterface, arch, pers)
            if featlist:
                iface_features[dbinterface.name] = featlist

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
                if addr.usage == "zebra":
                    if addr.label not in vips:
                        vips[addr.label] = {"ip": addr.ip,
                                            "interfaces": [dbinterface.name]}
                        if addr.dns_records:
                            vips[addr.label]["fqdn"] = addr.dns_records[0]
                    else:
                        # Sanity check
                        if vips[addr.label]["ip"] != addr.ip:
                            raise ArgumentError("Zebra configuration mismatch: "
                                                "label %s has IP %s on "
                                                "interface %s, but IP %s on "
                                                "interface %s." %
                                                (addr.label, addr.ip,
                                                 dbinterface.name,
                                                 vips[addr.label]["ip"],
                                                 vips[addr.label]["interfaces"][0].name))
                        vips[addr.label]["interfaces"].append(dbinterface.name)

                    if dbinterface.name not in transit_interfaces:
                        transit_interfaces.append(dbinterface.name)

                    continue
                elif addr.usage != "system":
                    continue

                net = addr.network

                if addr.label == "":
                    if net.routers:
                        local_rtrs = select_routers(self.dbhost.machine, net.routers)
                        gateway = local_rtrs[0]
                        if is_default_route(dbinterface):
                            routers[dbinterface.name] = local_rtrs
                    else:
                        # Fudge the gateway as the first available ip
                        gateway = net.network[1]

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
                for route in static_routes:
                    if route.gateway_ip == default_gateway:
                        continue
                    ifdesc["route"].append({"address": route.destination.ip,
                                            "netmask": route.destination.netmask,
                                            "gateway": route.gateway_ip})
                if not ifdesc["route"]:
                    del ifdesc["route"]

            interfaces[dbinterface.name] = ifdesc

        personality_template = "personality/%s/config" % \
                self.dbhost.personality.name
        os_template = self.dbhost.operating_system.cfg_path + '/config'

        services = []
        required_services = set(arch.services + pers.services)

        for si in self.dbhost.services_used:
            required_services.discard(si.service)
            services.append(si.cfg_path + '/client/config')
        if required_services:
            raise IncompleteError("Host %s is missing required services %s." %
                                  (self.name, required_services))

        provides = []
        for si in self.dbhost.services_provided:
            provides.append('%s/server/config' % si.cfg_path)

        # Ensure used/provided services have a stable order
        services.sort()
        provides.sort()

        templates = []
        templates.append("archetype/base")
        templates.append(os_template)

        for feature in model_features(self.dbhost.machine.model, arch, pers):
            templates.append("%s/config" % feature.cfg_path)

        templates.extend(services)
        templates.extend(provides)

        (pre_features, post_features) = personality_features(pers)
        for feature in pre_features:
            templates.append("%s/config" % feature.cfg_path)

        templates.append(personality_template)

        if self.dbhost.cluster:
            clplenary = PlenaryClusterClient(self.dbhost.cluster)
            templates.append(clplenary.plenary_template)
        elif pers.cluster_required:
            raise IncompleteError("Host %s personality %s requires cluster "
                                  "membership." % (self.name, pers.name))

        for feature in post_features:
            templates.append("%s/config" % feature.cfg_path)

        templates.append("archetype/final")

        eon_id_set = set([grn.eon_id for grn in self.dbhost.grns])
        eon_id_set |= set([grn.eon_id for grn in pers.grns])
        eon_id_list = list(eon_id_set)
        eon_id_list.sort()

        # Okay, here's the real content
        arcdir = arch.name
        lines.append("# this is an %s host, so all templates should be sourced from there" % arch.name)
        lines.append("variable LOADPATH = %s;" % pan([arcdir]))
        lines.append("")
        lines.append("include { 'pan/units' };")
        lines.append("include { 'pan/functions' };")
        lines.append("")
        pmachine = PlenaryMachineInfo(self.dbhost.machine)
        lines.append("'/hardware' = %s;" %
                     pan(StructureTemplate(pmachine.plenary_template)))

        lines.append("")
        lines.append("'/system/network/interfaces' = %s;" % pan(interfaces))
        lines.append("'/system/network/primary_ip' = %s;" %
                     pan(self.dbhost.machine.primary_ip))
        if default_gateway:
            lines.append("'/system/network/default_gateway' = %s;" %
                         pan(default_gateway))
        if vips:
            lines.append('"/system/network/vips" = %s;' % pan(vips))
        if routers:
            lines.append('"/system/network/routers" = %s;' % pan(routers))
        lines.append("")

        for iface in sorted(iface_features.keys()):
            lines.append('variable CURRENT_INTERFACE = "%s";' % iface)
            for feature in iface_features[iface]:
                # Same forgiveness for interface model features
                lines.append('include { "%s/config" };' % feature.cfg_path)
            lines.append("")

        lines.append("'/system/build' = %s;" % pan(self.dbhost.status.name))
        if eon_id_list:
            lines.append('"/system/eon_ids" = %s;' % pan(eon_id_list))
        if self.dbhost.cluster:
            lines.append("'/system/cluster/name' = %s;" % pan(self.dbhost.cluster.name))
        lines.append("")
        for resource in sorted(self.dbhost.resources):
            lines.append("'/system/resources/%s' = push(%s);" % (
                         resource.resource_type,
                         pan(StructureTemplate(resource.template_base +
                                               '/config'))))
        lines.append("")
        for template in templates:
            lines.append("include { %s };" % pan(template))
        lines.append("")

        return

    def write(self, *args, **kwargs):
        # Don't bother writing plenary files for dummy aurora hardware or for
        # non-compilable archetypes.
        if self.dbhost.machine.model.machine_type == 'aurora_node' or \
           not self.dbhost.archetype.is_compileable:
            return 0
        return Plenary.write(self, *args, **kwargs)


class PlenaryNamespacedHost(PlenaryToplevelHost):
    """
    A plenary template describing a host, namespaced by DNS domain
    """
    def __init__(self, dbhost, logger=LOGGER):
        PlenaryToplevelHost.__init__(self, dbhost, logger=logger)
        self.name = dbhost.fqdn
        self.plenary_core = dbhost.machine.primary_name.fqdn.dns_domain.name
        self.plenary_template = "%(plenary_core)s/%(name)s" % self.__dict__
