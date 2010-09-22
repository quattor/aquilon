# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
"""Contains the logic for `aq show hostiplist`."""


from sqlalchemy.orm import contains_eager, aliased

from aquilon.server.broker import BrokerCommand
from aquilon.server.formats.host import HostIPList
from aquilon.aqdb.model import (AddressAssignment, VlanInterface, Interface,
                                HardwareEntity, Personality, Machine, Host,
                                Archetype, PrimaryNameAssociation,
                                FutureARecord, System, DnsDomain)


class CommandShowHostIPList(BrokerCommand):

    default_style = "csv"

    def render(self, session, archetype, **arguments):
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

        # System and DnsRecord are used twice, so be certain which instance
        # is used where
        addr_dnsrec = aliased(FutureARecord, name="addr_dnsrec")
        addr_domain = aliased(DnsDomain, name="addr_domain")
        pna_dnsrec = aliased(System, name="pna_dnsrec")
        pna_domain = aliased(DnsDomain, name="pna_dnsdomain")

        q = session.query(AddressAssignment)
        q = q.join((addr_dnsrec, addr_dnsrec.ip == AddressAssignment.ip))
        q = q.join((addr_domain, addr_dnsrec.dns_domain_id ==
                    addr_domain.id))

        # Make sure we pick up the right System/DnsRecord instance
        q = q.options(contains_eager("dns_records", alias=addr_dnsrec))
        q = q.options(contains_eager("dns_records.dns_domain",
                                     alias=addr_domain))

        q = q.reset_joinpoint()
        q = q.join(VlanInterface, Interface, HardwareEntity)

        # If archetype was given, select only the matching hosts. Otherwise,
        # exclude aurora hosts.
        if archetype:
            q = q.filter(HardwareEntity.id.in_(archq.subquery()))
        else:
            q = q.filter(~HardwareEntity.id.in_(archq.subquery()))

        q = q.outerjoin(PrimaryNameAssociation)
        q = q.outerjoin((pna_dnsrec, PrimaryNameAssociation.dns_record_id ==
                         pna_dnsrec.id))
        q = q.outerjoin((pna_domain, pna_dnsrec.dns_domain_id == pna_domain.id))
        q = q.options(contains_eager('vlan'))
        q = q.options(contains_eager('vlan.interface'))
        q = q.options(contains_eager('vlan.interface.hardware_entity'))
        q = q.options(contains_eager("vlan.interface.hardware_entity."
                                     "_primary_name_asc"))

        # Make sure we pick up the right System/DnsRecord instance
        q = q.options(contains_eager("vlan.interface.hardware_entity."
                                     "_primary_name_asc.dns_record",
                                     alias=pna_dnsrec))
        q = q.options(contains_eager("vlan.interface.hardware_entity."
                                     "_primary_name_asc.dns_record.dns_domain",
                                    alias=pna_domain))

        q = q.order_by(addr_dnsrec.name, addr_domain.name)

        # FIXME: this list does not contain the addresses reserved for dynamic
        # DHCP. Is this a bug or a feature?
        iplist = HostIPList()
        for addr in q.all():
            entry = [addr.fqdns[0], addr.ip]
            hwent = addr.vlan.interface.hardware_entity
            # FIXME: the exclusion of management interfaces is questionable, but
            # matches the previous behavior
            if hwent.primary_name and addr.ip != hwent.primary_ip and \
               addr.vlan.interface.interface_type != 'management':
                entry.append(hwent.fqdn)
            else:
                entry.append("")
            iplist.append(entry)

        return iplist
