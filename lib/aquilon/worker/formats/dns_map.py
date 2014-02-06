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
""" DNS Domain Map formatter. """


from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.aqdb.model import DnsMap


class DnsMapFormatter(ObjectFormatter):
    def format_raw(self, dns_map, indent=""):
        details = []
        details.append(indent + "{0:c}: {0.name} Map: "
                       "{1}".format(dns_map.dns_domain, dns_map.location))
        details.append(indent + "  Position: %s" % dns_map.position)
        if dns_map.comments:
            details.append(indent + "  Comments: %s" % dns_map.comments)
        return "\n".join(details)

    def csv_fields(self, dns_map):
        yield (dns_map.dns_domain.fqdn, dns_map.location.location_type,
               dns_map.location.name, dns_map.comments)

ObjectFormatter.handlers[DnsMap] = DnsMapFormatter()
