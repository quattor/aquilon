# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014,2015  Contributor
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
"""Virtual switch formatter."""

from operator import attrgetter
from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.aqdb.model import VirtualSwitch


class VirtualSwitchFormatter(ObjectFormatter):
    def format_raw(self, vswitch, indent="", embedded=True,
                   indirect_attrs=True):
        details = [indent + "{0:c}: {0.name}".format(vswitch)]
        if vswitch.comments:
            details.append(indent + "  Comments: %s" % vswitch.comments)
        for pg in sorted(vswitch.port_groups,
                         key=attrgetter("usage", "network_tag")):
            details.append(indent + "  Port Group: %s" % pg.name)
            details.append(indent + "    Network: %s" % pg.network.ip)

        if not embedded:
            for host in sorted(vswitch.hosts, key=attrgetter("fqdn")):
                details.append(indent + "  Bound to {0:c}: {0!s}".format(host))

            for cluster in sorted(vswitch.clusters, key=attrgetter("name")):
                details.append(indent + "  Bound to {0:c}: {0!s}".format(cluster))

        return "\n".join(details)

    def fill_proto(self, vswitch, skeleton, embedded=True,
                   indirect_attrs=True):
        skeleton.name = str(vswitch.name)
        for pg in vswitch.port_groups:
            pg_msg = skeleton.portgroups.add()
            pg_msg.ip = str(pg.network.ip)
            pg_msg.cidr = pg.network.cidr
            pg_msg.network_tag = pg.network_tag
            pg_msg.usage = str(pg.usage)

ObjectFormatter.handlers[VirtualSwitch] = VirtualSwitchFormatter()
