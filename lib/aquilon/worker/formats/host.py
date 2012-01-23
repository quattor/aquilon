# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013  Contributor
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
"""Host formatter."""

from aquilon.aqdb.model import Host
from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.list import ListFormatter


# TODO: this formatter is kept only for the protobuf stuff, otherwise
# MachineFormatter does everything
class HostFormatter(ObjectFormatter):
    def format_proto(self, host, container):
        skeleton = container.hosts.add()
        self.add_host_data(skeleton, host)
        for si in host.services_used:
            srv_msg = skeleton.services_used.add()
            srv_msg.service = si.service.name
            srv_msg.instance = si.name
        for si in host.services_provided:
            srv_msg = skeleton.services_provided.add()
            srv_msg.service = si.service.name
            srv_msg.instance = si.name

    def format_raw(self, host, indent=""):
        return self.redirect_raw(host.hardware_entity, indent)

ObjectFormatter.handlers[Host] = HostFormatter()


class GrnHostList(list):
    """By convention, holds a list of hosts to be formatted to provide
       (grn-only) data."""
    pass

class GrnHostListFormatter(ListFormatter):
    def format_raw(self, shlist, indent=""):
        details = []
        for host in shlist:
            if host.hardware_entity.primary_name:
                details.append(indent + "Primary Name: "
                                        "{0:a}".format(host.hardware_entity.primary_name))
            hstr = "  Owned by {0:c}: {0.grn}".format(host.effective_owner_grn)

            if host.effective_owner_grn == host.owner_grn:
                details.append(indent + hstr)
            else:
                details.append(indent + hstr + " [inherited]")

            eon_targets = [grn.target for grn in host._grns]
            for (target, eon_id_set) in host.effective_grns.iteritems():
                inherited = ""
                eon_id_list = list(eon_id_set)
                eon_id_list.sort()
                if target not in set(eon_targets):
                    inherited = " [inherited]"
                for grn_rec in eon_id_list:
                    details.append(indent + "  Used by {0:c}: {0.grn} "
                                            "[target: {1}]{2}"
                                            .format(grn_rec, target, inherited))
        return "\n".join(details)

    def format_proto(self, hostlist, container):
        for host in hostlist:
            msg = container.hosts.add()
            msg.hostname = str(host.hardware_entity.primary_name)
            msg.domain.name = str(host.branch.name)
            msg.domain.owner = str(host.branch.owner.name)
            msg.status = str(host.status.name)
            msg.owner_eonid = host.effective_owner_grn.eon_id
            ##personality
            msg.personality.archetype.name = str(host.archetype)
            msg.personality.name = str(host.personality)
            msg.personality.host_environment = str(host.personality.host_environment)
            msg.personality.owner_eonid = host.personality.owner_eon_id
            ## eon id maps TBD need both effective and actual
            for grn_rec in sorted(host.personality._grns, key=lambda x: x.target):
                map = msg.personality.eonid_maps.add()
                map.target = grn_rec.target
                map.eonid = grn_rec.eon_id

            for (target, eon_id_set) in host.effective_grns.iteritems():
                for grn_rec in list(eon_id_set):
                    map = msg.eonid_maps.add()
                    map.target = target
                    map.eonid = grn_rec.eon_id

ObjectFormatter.handlers[GrnHostList] = GrnHostListFormatter()


class HostIPList(list):
    """ By convention, holds tuples of host_name, interface_ip, primary.
        The third field is only used for auxiliary systems, and
        supplies the primary host name.  This allows reverse lookups
        to resolve back to the primary name."""
    pass


class HostIPListFormatter(ListFormatter):
    def csv_fields(self, hostips):
        return hostips

ObjectFormatter.handlers[HostIPList] = HostIPListFormatter()


class HostMachineList(list):
    """By convention, holds Host objects."""
    pass


class HostMachineListFormatter(ListFormatter):
    def csv_fields(self, host):
        return (host.fqdn, host.hardware_entity.label)

ObjectFormatter.handlers[HostMachineList] = HostMachineListFormatter()
