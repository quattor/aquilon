# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
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
from sqlalchemy.orm import (relation, backref, mapper, deferred, object_session,
                            validates)
from sqlalchemy.orm.attributes import instance_state

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Network, DnsRecord, Fqdn
from aquilon.aqdb.column_types import IPV4

_TN = 'a_record'


class ARecord(DnsRecord):
    __tablename__ = _TN
    __mapper_args__ = {'polymorphic_identity': _TN}
    _class_label = 'DNS Record'

    dns_record_id = Column(Integer, ForeignKey('dns_record.id',
                                               name='%s_dns_record_fk' % _TN,
                                               ondelete='CASCADE'),
                           primary_key=True)

    ip = Column(IPV4, nullable=False)

    network_id = Column(Integer, ForeignKey('network.id',
                                            name='%s_network_fk' % _TN),
                        nullable=False)

    reverse_ptr_id = Column(Integer, ForeignKey('fqdn.id',
                                                name='%s_reverse_fk' % _TN,
                                                ondelete='SET NULL'),
                            nullable=True)

    network = relation(Network, backref=backref('dns_records',
                                                passive_deletes=True))

    reverse_ptr = relation(Fqdn, primaryjoin=reverse_ptr_id == Fqdn.id,
                           backref=backref('reverse_entries',
                                           passive_deletes=True))

    def __format__(self, format_spec):
        if format_spec != "a":
            return super(ARecord, self).__format__(format_spec)
        return "%s [%s]" % (self.fqdn, self.ip)

    def __init__(self, ip=None, network=None, fqdn=None, **kwargs):
        if not network:  # pragma: no cover
            raise ValueError("network argument is missing")
        if ip not in network.network:  # pragma: no cover
            raise ValueError("IP not inside network")

        if not fqdn:  # pragma: no cover
            raise ValueError("fqdn cannot be empty")

        # We can't share both the IP and the FQDN with an other A record. Only
        # do the query if the FQDN is already persistent
        if instance_state(fqdn).has_identity:
            session = object_session(fqdn)
            if not session:  # pragma: no cover
                raise ValueError("fqdn must be already part of a session")

            # Disable autoflush because self is not ready to be pushed to the DB
            # yet
            with session.no_autoflush:
                q = session.query(ARecord.id)
                q = q.filter_by(ip=ip)
                q = q.filter_by(network=network)
                q = q.filter_by(fqdn=fqdn)
                if q.all():  # pragma: no cover
                    raise ArgumentError("%s, ip %s already exists." %
                                        (self._get_class_label(), ip))

        super(ARecord, self).__init__(ip=ip, network=network, fqdn=fqdn,
                                      **kwargs)

    @validates('reverse_ptr')
    def _validate_reverse_ptr(self, key, value):
        return self.validate_reverse_ptr(key, value)

    def validate_reverse_ptr(self, key, value):
        if value and self.fqdn.dns_environment != value.dns_environment:  # pragma: no cover
            raise ValueError("DNS environment mismatch: %s != %s" %
                             (self.fqdn.dns_environment, value.dns_environment))
        return value


arecord = ARecord.__table__  # pylint: disable=C0103
arecord.primary_key.name = '%s_pk' % _TN
# TODO: index on ip?

arecord.info['unique_fields'] = ['fqdn']
arecord.info['extra_search_fields'] = ['ip', 'network', 'dns_environment']

dns_record = DnsRecord.__table__  # pylint: disable=C0103
fqdn = Fqdn.__table__  # pylint: disable=C0103

# Create a secondary mapper on the join of the DnsRecord and Fqdn tables
dns_fqdn_mapper = mapper(ARecord,
                         arecord.join(dns_record)
                         .join(fqdn, dns_record.c.fqdn_id == fqdn.c.id),
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
                             'fqdn': relation(Fqdn, lazy=False, innerjoin=True,
                                              primaryjoin=ARecord.fqdn_id == Fqdn.id)
                         },
                         polymorphic_identity=_TN,
                         primary_key=arecord.c.dns_record_id,
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

    dns_record_id = Column(Integer, ForeignKey('%s.dns_record_id' % _TN,
                                               name='dynamic_stub_arecord_fk',
                                               ondelete='CASCADE'),
                           primary_key=True)

    def validate_reverse_ptr(self, key, value):
        super(DynamicStub, self).validate_reverse_ptr(key, value)
        if value:
            raise ValueError("The reverse PTR record cannot be set for "
                             "DNS records used for dynamic DHCP.")
        return value


dynstub = DynamicStub.__table__  # pylint: disable=C0103
dynstub.primary_key.name = 'dynamic_stub_pk'
dynstub.info['unique_fields'] = ['fqdn']
dynstub.info['extra_search_fields'] = ['ip', 'network', 'dns_environment']

Network.dynamic_stubs = relation(DynamicStub, order_by=[DynamicStub.ip],
                                 viewonly=True)
