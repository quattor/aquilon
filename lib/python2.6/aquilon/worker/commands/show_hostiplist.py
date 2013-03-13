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
"""Contains the logic for `aq show hostiplist`."""


from sqlalchemy.orm import contains_eager, joinedload
from sqlalchemy.sql import and_

from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.formats.host import HostIPList
from aquilon.aqdb.model import (AddressAssignment, Interface, HardwareEntity,
                                Personality, Machine, Host, Archetype, ARecord,
                                Fqdn, DnsDomain, NetworkEnvironment, Network)


class CommandShowHostIPList(BrokerCommand):

    default_style = "csv"

    def render(self, session, archetype, **arguments):
        dbnet_env = NetworkEnvironment.get_unique_or_default(session)
        archq = session.query(Machine.id)
        archq = archq.join(Host, Personality)
        if archetype:
            dbarchetype = Archetype.get_unique(session, archetype, compel=True)
            archq = archq.filter(Personality.archetype == dbarchetype)
        else:
            # Ignore aurora hosts by default, since we're not authorative for
            # them (yet)
            dbarchetype = Archetype.get_unique(session, "aurora", compel=True)
            archq = archq.filter(Personality.archetype == dbarchetype)

        q = session.query(AddressAssignment)
        q = q.options(joinedload('dns_records'))
        q = q.join(Network)
        q = q.filter_by(network_environment=dbnet_env)
        q = q.options(contains_eager('network'))
        q = q.reset_joinpoint()

        q = q.join(Interface, HardwareEntity)
        q = q.options(contains_eager('interface'))
        q = q.options(contains_eager('interface.hardware_entity'))

        # If archetype was given, select only the matching hosts. Otherwise,
        # exclude aurora hosts.
        if archetype:
            q = q.filter(HardwareEntity.id.in_(archq.subquery()))
        else:
            q = q.filter(~HardwareEntity.id.in_(archq.subquery()))
        q = q.reset_joinpoint()

        iplist = HostIPList()
        for addr in q:
            hwent = addr.interface.hardware_entity
            # Only add the primary info for auxiliary addresses, not management
            # ones
            if hwent.primary_name and addr.ip != hwent.primary_ip and \
               addr.interface.interface_type != 'management' and \
               addr.service_address_id == None:
                primary = hwent.fqdn
            else:
                primary = None
            for fqdn in addr.fqdns:
                iplist.append((fqdn, addr.ip, primary))

        # Append addresses that are not bound to interfaces
        if not archetype:
            q = session.query(ARecord)
            q = q.join(ARecord.fqdn, DnsDomain)
            q = q.options(contains_eager("fqdn"),
                          contains_eager("fqdn.dns_domain"))
            q = q.reset_joinpoint()

            q = q.join(Network)
            q = q.filter_by(network_environment=dbnet_env)
            q = q.options(contains_eager("network"))
            q = q.reset_joinpoint()

            q = q.outerjoin((AddressAssignment,
                             and_(AddressAssignment.ip == ARecord.ip,
                                  AddressAssignment.dns_environment_id ==
                                  Fqdn.dns_environment_id)))
            q = q.filter(AddressAssignment.id == None)

            q = q.order_by(Fqdn.name, DnsDomain.name)

            for entry in q:
                iplist.append((str(entry.fqdn), entry.ip, None))

        return iplist
