# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015  Contributor
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
from six import iteritems

from sqlalchemy.inspection import inspect

from aquilon.exceptions_ import InternalError, IncompleteError
from aquilon.aqdb.model import (Host, VlanInterface, BondingInterface,
                                BridgeInterface)
from aquilon.worker.locks import CompileKey, PlenaryKey
from aquilon.worker.templates import (Plenary, ObjectPlenary, StructurePlenary,
                                      PlenaryCollection, PlenaryClusterClient,
                                      PlenaryResource, PlenaryPersonalityBase,
                                      PlenaryServiceInstanceClientDefault,
                                      PlenaryServiceInstanceServerDefault)
from aquilon.worker.templates.panutils import (StructureTemplate, PanValue,
                                               pan_assign, pan_append,
                                               pan_include)
from aquilon.utils import nlist_key_re

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
    def __init__(self, dbhost, logger=LOGGER, allow_incomplete=True):
        super(PlenaryHost, self).__init__(logger=logger,
                                          allow_incomplete=allow_incomplete)

        if not isinstance(dbhost, Host):
            raise InternalError("PlenaryHost called with %s instead of Host" %
                                dbhost.__class__.name)
        self.dbobj = dbhost
        self.append(PlenaryHostObject.get_plenary(dbhost,
                                                  allow_incomplete=allow_incomplete))
        self.append(PlenaryHostData.get_plenary(dbhost,
                                                allow_incomplete=allow_incomplete))

Plenary.handlers[Host] = PlenaryHost


class PlenaryHostData(StructurePlenary):
    prefix = "hostdata"

    @classmethod
    def template_name(cls, dbhost):
        return cls.prefix + "/" + str(dbhost.fqdn)

    def body(self, lines):
        interfaces = dict()
        routers = {}
        default_gateway = None

        # FIXME: Enforce that one of the interfaces is marked boot?
        for dbinterface in self.dbobj.hardware_entity.interfaces:
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
                net = addr.network

                if addr.label == "":
                    if net.routers:
                        local_rtrs = select_routers(self.dbobj.hardware_entity,
                                                    net.routers)
                        gateway = local_rtrs[0]
                        if is_default_route(dbinterface):
                            routers[dbinterface.name] = local_rtrs
                    elif net.network.numhosts >= 4:
                        # No routers defided, fall back to the default
                        gateway = net.network[net.default_gateway_offset]
                    else:
                        gateway = None

                    # TODO: generate appropriate routing policy if there are
                    # multiple interfaces marked as default_route
                    if not default_gateway and is_default_route(dbinterface):
                        default_gateway = gateway

                    ifdesc["ip"] = addr.ip
                    ifdesc["netmask"] = net.netmask
                    ifdesc["broadcast"] = net.broadcast
                    if gateway:
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

                static_routes |= set(net.personality_static_routes(self.dbobj.personality_stage))

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
        hwplenary = Plenary.get_plenary(self.dbobj.hardware_entity)
        path = hwplenary.template_name(self.dbobj.hardware_entity)
        pan_assign(lines, "hardware", StructureTemplate(path))

        lines.append("")
        for name in sorted(interfaces):
            # This is ugly. We can't blindly escape, because that would affect
            # e.g. VLAN interfaces. Calling unescape() for a non-escaped VLAN
            # interface name is safe though, so we can hopefully get rid of this
            # once the templates are changed to call unescape().
            if nlist_key_re.match(name):
                pan_assign(lines, "system/network/interfaces/%s" % name,
                           interfaces[name])
            else:
                pan_assign(lines, "system/network/interfaces/{%s}" % name,
                           interfaces[name])

        if self.dbobj.hardware_entity.primary_ip:
            pan_assign(lines, "system/network/primary_ip",
                       self.dbobj.hardware_entity.primary_ip)

        if default_gateway:
            pan_assign(lines, "system/network/default_gateway",
                       default_gateway)

        if routers:
            pan_assign(lines, "system/network/routers", routers)

        lines.append("")

        pan_assign(lines, "system/build", self.dbobj.status.name)
        pan_assign(lines, "system/advertise_status", self.dbobj.advertise_status)

        # process grns
        eon_id_map = self.dbobj.effective_grns

        for target, eon_id_set in iteritems(eon_id_map):
            eon_id_list = sorted(grn.eon_id for grn in eon_id_set)
            pan_assign(lines, "system/eon_id_maps/%s" % target, eon_id_list)

        pan_assign(lines, "system/owner_eon_id", self.dbobj.effective_owner_grn.eon_id)

        if self.dbobj.cluster:
            pan_assign(lines, "system/cluster/name", self.dbobj.cluster.name)
            pan_assign(lines, "system/cluster/node_index",
                       self.dbobj._cluster.node_index)
            if self.dbobj.cluster.metacluster:
                pan_assign(lines, "system/cluster/metacluster/name",
                           self.dbobj.cluster.metacluster.name)

        if self.dbobj.virtual_switch:
            pan_assign(lines, "system/virtual_switch",
                       self.dbobj.virtual_switch.name)

        if self.dbobj.resholder:
            lines.append("")
            for resource in sorted(self.dbobj.resholder.resources,
                                   key=attrgetter('resource_type', 'name')):
                res_path = PlenaryResource.template_name(resource)
                pan_append(lines, "system/resources/" + resource.resource_type,
                           StructureTemplate(res_path))


class PlenaryHostObject(ObjectPlenary):
    """
    A plenary template for a host, stored at the toplevel of the profiledir
    """

    @classmethod
    def template_name(cls, dbhost):
        return str(dbhost.fqdn)

    def get_key(self, exclusive=True):
        keylist = [super(PlenaryHostObject, self).get_key(exclusive=exclusive)]

        if not inspect(self.dbobj).deleted:
            keylist.append(PlenaryKey(exclusive=False,
                                      personality=self.dbobj.personality_stage,
                                      logger=self.logger))
            keylist.extend(PlenaryKey(exclusive=False, service_instance=si,
                                      logger=self.logger)
                           for si in self.dbobj.services_used)
            keylist.extend(PlenaryKey(exclusive=False,
                                      service_instance=srv.service_instance,
                                      logger=self.logger)
                           for srv in self.dbobj.services_provided)

            if self.dbobj.cluster:
                keylist.append(PlenaryKey(exclusive=False,
                                          cluster_member=self.dbobj.cluster,
                                          logger=self.logger))
            if self.dbobj.virtual_switch:
                keylist.append(PlenaryKey(exclusive=False,
                                          virtual_switch=self.dbobj.virtual_switch,
                                          logger=self.logger))
        return CompileKey.merge(keylist)

    def body(self, lines):
        dbstage = self.dbobj.personality_stage

        # FIXME: Enforce that one of the interfaces is marked boot?
        for dbinterface in self.dbobj.hardware_entity.interfaces:
            # Management interfaces are not configured at the host level
            if dbinterface.interface_type == 'management':
                continue

        services = []
        required_services = self.dbobj.required_services

        for si in self.dbobj.services_used:
            required_services.discard(si.service)
            services.append(PlenaryServiceInstanceClientDefault.template_name(si))
        if required_services:
            missing = ", ".join(sorted(srv.name for srv in required_services))
            raise IncompleteError("{0} is missing the following required "
                                  "services, please run 'aq reconfigure': "
                                  "{1!s}.".format(self.dbobj, missing))

        provides = []
        for srv in self.dbobj.services_provided:
            si = srv.service_instance
            provides.append(PlenaryServiceInstanceServerDefault.template_name(si))

        # Ensure used/provided services have a stable order
        services.sort()
        provides.sort()

        # Okay, here's the real content
        pan_include(lines, ["pan/units", "pan/functions"])
        lines.append("")

        path = PlenaryHostData.template_name(self.dbobj)
        pan_assign(lines, "/",
                   StructureTemplate(path,
                                     {"metadata": PanValue("/metadata")}))
        pan_include(lines, "archetype/base")

        opsys = self.dbobj.operating_system
        pan_include(lines, "os/%s/%s/config" % (opsys.name, opsys.version))

        pan_include(lines, services)
        pan_include(lines, provides)

        path = PlenaryPersonalityBase.template_name(dbstage)
        pan_include(lines, path)

        if self.dbobj.cluster:
            pan_include(lines,
                        PlenaryClusterClient.template_name(self.dbobj.cluster))
        elif dbstage.personality.cluster_required:
            raise IncompleteError("{0} requires cluster membership, please "
                                  "run 'aq cluster'."
                                  .format(dbstage.personality))
        pan_include(lines, "archetype/final")
