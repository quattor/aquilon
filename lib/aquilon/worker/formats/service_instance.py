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
"""ServiceInstance formatter."""

from operator import attrgetter

from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.aqdb.model import ServiceInstance, ServiceInstanceServer


class ServiceInstanceServerFormatter(ObjectFormatter):
    def format_raw(self, srv, indent="", embedded=True, indirect_attrs=True):
        msg = str(srv.fqdn)
        attrs = []

        if srv.alias:
            attrs.append("alias")
        if srv.cluster:
            attrs.append("cluster: %s" % srv.cluster.name)
        if srv.host and srv.host.fqdn != srv.fqdn:
            attrs.append("host: %s" % srv.host.fqdn)
        if srv.service_address:
            attrs.append("service_address: %s" % srv.service_address.name)

        # If the service is bound to the host object only, then the actual
        # implementation may either provide the service on all IP addresses the
        # host has, or just on the primary IP address only. Since the broker has
        # no way to know that, don't display any IP address in this case.
        if srv.ip and (not srv.host or srv.service_address or
                       srv.address_assignment):
            attrs.append("IP: %s" % srv.ip)

        if attrs:
            msg += " [" + ", ".join(attrs) + "]"

        return indent + "Server Binding: %s" % msg

ObjectFormatter.handlers[ServiceInstanceServer] = ServiceInstanceServerFormatter()


class ServiceInstanceFormatter(ObjectFormatter):
    def format_raw(self, si, indent="", embedded=True, indirect_attrs=True):
        details = [indent + "Service: %s Instance: %s" % (si.service.name,
                                                          si.name)]
        for srv in si.servers:
            details.append(self.redirect_raw(srv, indent + "  "))
        for map in si.service_map:
            details.append(indent + "  Service Map: {0}".format(map.mapped_to))
        for pmap in si.personality_service_map:
            details.append(indent +
                           "  Personality Service Map: %s "
                           "(Archetype %s Personality %s)" %
                           (format(pmap.mapped_to),
                            pmap.personality.archetype.name,
                            pmap.personality.name))
        details.append(indent + "  Maximum Client Count: %s" %
                       ServiceInstanceFormatter.get_max_client_count(si))
        details.append(indent + "  Client Count: %d" % si.client_count)
        if si.comments:
            details.append(indent + "  Comments: %s" % si.comments)
        return "\n".join(details)

    def fill_proto(self, si, skeleton, embedded=True, indirect_attrs=True):
        # skeleton can be either NamedServiceInstance, ServiceInstance or
        # Service, depending on the caller
        if skeleton.DESCRIPTOR.name == 'NamedServiceInstance':
            skeleton.service = si.service.name
            skeleton.instance = si.name
            return

        if skeleton.DESCRIPTOR.name == 'ServiceInstance':
            si_msg = skeleton
        else:
            skeleton.name = si.service.name
            si_msg = skeleton.serviceinstances.add()

        si_msg.name = si.name

        if indirect_attrs:
            for srv in sorted(si.servers, key=attrgetter("position")):
                # In all of the following we always calculate a target IP and
                # FQDN.  All of the above cases can be infered by the
                # information provided. The valid combinations are as follows:
                #  - Alias (no IP address)
                #  - Host (with or without an IP address)
                #  - Host + address_assignment
                #  - Host + service_address
                #  - Cluster + service_address
                target_ip = None
                target_fqdn = None
                srv_msg = si_msg.provider.add()

                if srv.alias:
                    target_fqdn = str(srv.alias.fqdn)
                    # There is no IP address for an alias
                elif srv.host:
                    # Add minimum amount of the host message.  This should be
                    # just the FQDN, but we have to add hostname (short)
                    # as its required.  The ip is added so you can determin if
                    # a address_assignment has been used.
                    hw = srv.host.hardware_entity
                    host_msg = srv_msg.host
                    host_msg.hostname = hw.primary_name.fqdn.name

                    # Default to the hosts primary IP and name
                    host_msg.fqdn = str(hw.primary_name.fqdn)
                    target_fqdn = host_msg.fqdn

                    if hw.primary_ip:
                        host_msg.ip = str(hw.primary_ip)
                        target_ip = host_msg.ip

                    # TODO: The following is being kept for backwards
                    # compatability the ServiceInstanceProvider is preferable
                    self.redirect_proto(srv.host, si_msg.servers.add(),
                                        indirect_attrs=False)
                elif srv.cluster:
                    clus_msg = srv_msg.cluster
                    clus_msg.name = srv.cluster.name
                    # Clusters must have a service_address so we leave the
                    # target addresses to be filled in later

                # Where address_assignment or service_address are supplied
                # these should override the default targets
                if srv.address_assignment:
                    target_ip = str(srv.address_assignment.ip)
                    target_fqdn = str(srv.address_assignment.fqdns[0])
                elif srv.service_address:
                    srv_msg.service_address.ip = str(srv.service_address.ip)
                    srv_msg.service_address.fqdn = str(srv.service_address.dns_record)
                    target_ip = str(srv.service_address.ip)
                    target_fqdn = str(srv.service_address.dns_record.fqdn)

                # Finally add the target ip and fqdn
                if target_ip:
                    srv_msg.target_ip = target_ip
                srv_msg.target_fqdn = target_fqdn

    # Applies to service_instance/share as well.
    @classmethod
    def get_max_client_count(cls, si):
        max_clients = si.max_clients
        if max_clients is None:
            if si.service.max_clients is None:
                max_clients = "Default (Unlimited)"
            else:
                max_clients = "Default (%s)" % si.service.max_clients

        return max_clients

ObjectFormatter.handlers[ServiceInstance] = ServiceInstanceFormatter()
