# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011  Contributor
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
""" Representation of DNS A records """

from sqlalchemy import Integer, Column, ForeignKey
from sqlalchemy.orm import relation, backref, mapper

from aquilon.aqdb.model import Network, DnsRecord, Fqdn
from aquilon.aqdb.column_types import IPV4


class ARecord(DnsRecord):
    __tablename__ = 'a_record'
    __mapper_args__ = {'polymorphic_identity': 'a_record'}
    _class_label = 'DNS Record'

    dns_record_id = Column(Integer, ForeignKey('dns_record.id',
                                               name='A_RECORD_DNS_RECORD_FK',
                                               ondelete='CASCADE'),
                           primary_key=True)

    ip = Column(IPV4, nullable=False)

    # ON DELETE SET NULL and later passive_deletes=True helps refresh_network in
    # case of network splits/merges
    network_id = Column(Integer, ForeignKey('network.id',
                                            name='A_RECORD_NETWORK_FK',
                                            ondelete="SET NULL"),
                        nullable=True)

    network = relation(Network, backref=backref('dns_records',
                                                passive_deletes=True))

    def __format__(self, format_spec):
        if format_spec != "a":
            return super(ARecord, self).__format__(format_spec)
        return "%s [%s]" % (self.fqdn, self.ip)


arecord = ARecord.__table__  # pylint: disable-msg=C0103, E1101
arecord.primary_key.name = 'a_record_pk'
# TODO: index on ip?

arecord.info['unique_fields'] = ['fqdn']
arecord.info['extra_search_fields'] = ['ip']

# Create a secondary mapper on the join of the DnsRecord and Fqdn tables
dns_fqdn_mapper = mapper(ARecord, ARecord.__table__.join(DnsRecord.__table__).join(Fqdn.__table__),
                         exclude_properties=[Fqdn.__table__.c.id,
                                             Fqdn.__table__.c.creation_date],
                         primary_key=[ARecord.__table__.c.dns_record_id],
                         non_primary=True)


class DynamicStub(ARecord):
    """
        DynamicStub is a hack to handle stand alone DNS records for dynamic
        hosts prior to having a properly reworked set of tables for DNS
        information. It should not be used by anything other than to create host
        records for virtual machines using names similar to
        'dynamic-1-2-3-4.subdomain.ms.com'
    """
    __tablename__ = 'dynamic_stub'
    __mapper_args__ = {'polymorphic_identity': 'dynamic_stub'}
    _class_label = 'Dynamic Stub'

    dns_record_id = Column(Integer, ForeignKey('a_record.dns_record_id',
                                               name='dynamic_stub_arecord_fk',
                                               ondelete='CASCADE'),
                           primary_key=True)


dynstub = DynamicStub.__table__  # pylint: disable-msg=C0103, E1101
dynstub.primary_key.name = 'dynamic_stub_pk'
