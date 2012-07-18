# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011,2012  Contributor
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
from sqlalchemy.orm import relation, backref, mapper, deferred, object_session
from sqlalchemy.orm.attributes import instance_state

from aquilon.exceptions_ import ArgumentError
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

    network_id = Column(Integer, ForeignKey('network.id',
                                            name='A_RECORD_NETWORK_FK'),
                        nullable=False)

    network = relation(Network, backref=backref('dns_records',
                                                passive_deletes=True))

    def __format__(self, format_spec):
        if format_spec != "a":
            return super(ARecord, self).__format__(format_spec)
        return "%s [%s]" % (self.fqdn, self.ip)

    def __init__(self, ip=None, network=None, fqdn=None, **kwargs):
        if not network:
            raise ValueError("network argument is missing")
        if ip not in network.network:
            raise ValueError("IP not inside network")

        if not fqdn:
            raise ValueError("fqdn cannot be empty")

        # We can't share both the IP and the FQDN with an other A record. Only
        # do the query if the FQDN is already persistent
        if instance_state(fqdn).has_identity:
            session = object_session(fqdn)
            if not session:
                raise ValueError("fqdn must be already part of a session")

            # Disable autoflush temporarily
            flush_state = session.autoflush
            session.autoflush = False

            q = session.query(ARecord.id)
            q = q.filter_by(ip=ip)
            q = q.filter_by(network=network)
            q = q.filter_by(fqdn=fqdn)
            if q.all():
                raise ArgumentError("%s, ip %s already exists." %
                                    (self._get_class_label(), ip))
            session.autoflush = flush_state

        super(ARecord, self).__init__(ip=ip, network=network, fqdn=fqdn,
                                      **kwargs)


arecord = ARecord.__table__  # pylint: disable=C0103
arecord.primary_key.name = 'a_record_pk'
# TODO: index on ip?

arecord.info['unique_fields'] = ['fqdn']
arecord.info['extra_search_fields'] = ['ip', 'network', 'dns_environment']

dns_record = DnsRecord.__table__  # pylint: disable=C0103
fqdn = Fqdn.__table__  # pylint: disable=C0103

# Create a secondary mapper on the join of the DnsRecord and Fqdn tables
dns_fqdn_mapper = mapper(ARecord, arecord.join(dns_record).join(fqdn),
                         # DnsRecord has a column with the same name
                         exclude_properties=[fqdn.c.creation_date],
                         properties={
                             # Both DnsRecord and Fqdn have a column named 'id'.
                             # Tell the ORM that DnsRecord.fqdn_id and Fqdn.id are
                             # really the same thing due to the join condition
                             'fqdn_id': [dns_record.c.fqdn_id, fqdn.c.id],

                             # Usually these columns are not needed, so don't
                             # load them automatically
                             'creation_date': deferred(dns_record.c.creation_date),
                             'comments': deferred(dns_record.c.comments),
                             # Make sure FQDNs are eager loaded when using this
                             # mapper
                             'fqdn': relation(Fqdn, lazy=False, innerjoin=True)
                         },
                         polymorphic_identity="a_record",
                         primary_key=arecord.c.dns_record_id,
                         non_primary=True)

# The secondary mapper does not know about the class inheritance, so we have to
# set the superclass explicitely
# This is http://www.sqlalchemy.org/trac/ticket/2151 - this workaround can be
# removed when we upgrade to SQLA 0.6.8
dns_fqdn_mapper._identity_class = DnsRecord


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


dynstub = DynamicStub.__table__  # pylint: disable=C0103
dynstub.primary_key.name = 'dynamic_stub_pk'
dynstub.info['unique_fields'] = ['fqdn']
dynstub.info['extra_search_fields'] = ['ip', 'network', 'dns_environment']

Network.dynamic_stubs = relation(DynamicStub, order_by=[DynamicStub.ip],
                                 viewonly=True)
