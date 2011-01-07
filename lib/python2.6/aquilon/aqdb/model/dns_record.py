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
""" Representation of DNS Data """

from datetime import datetime

from sqlalchemy import (Integer, DateTime, Sequence, String, Column, ForeignKey,
                        UniqueConstraint)
from sqlalchemy.orm import relation, deferred, backref

from aquilon.exceptions_ import InternalError, ArgumentError
from aquilon.aqdb.model import Base, DnsDomain
from aquilon.aqdb.model.dns_domain import parse_fqdn
from aquilon.aqdb.column_types import AqStr

_TN = "dns_record"

class DnsRecord(Base):
    """ Base class for a DNS Resource Record """

    __tablename__ = _TN
    _instance_label = 'fqdn'

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)

    name = Column(AqStr(63), nullable=False)

    dns_record_type = Column(AqStr(32), nullable=False)

    dns_domain_id = Column(Integer, ForeignKey('dns_domain.id',
                                               name='%s_dns_domain_fk' % _TN),
                           nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    comments = deferred(Column('comments', String(255), nullable=True))

    dns_domain = relation(DnsDomain, backref=backref("dns_records"))

    # The extra with_polymorphic: '*' means queries don't require
    # "q = q.with_polymorphic(DnsRecord.__mapper__.polymorphic_map.values())"
    __mapper_args__ = {'polymorphic_on': dns_record_type,
                       'polymorphic_identity': 'dns_record',
                       'with_polymorphic': '*'}

    @property
    def fqdn(self):
        return self.name + '.' + self.dns_domain.name

    @classmethod
    def get_unique(cls, session, *args, **kwargs):
        if "fqdn" in kwargs:
            (name, dbdns_domain) = parse_fqdn(session, kwargs.pop("fqdn"))
            kwargs["name"] = name
            kwargs["dns_domain"] = dbdns_domain
        return super(DnsRecord, cls).get_unique(session, *args, **kwargs)

    def __init__(self, session=None, *args, **kwargs):
        if "fqdn" in kwargs:
            if not session:
                raise InternalError("Passing fqdn to Session.__init__() needs "
                                    "a session.")
            (name, dbdns_domain) = parse_fqdn(session, kwargs.pop("fqdn"))
            kwargs["name"] = name
            kwargs["dns_domain"] = dbdns_domain
        super(DnsRecord, self).__init__(*args, **kwargs)

    @classmethod
    def get_or_create(cls, session, **kwargs):
        dns_record = cls.get_unique(session, **kwargs)
        if dns_record:
            return dns_record
        dns_record = cls(session=session, **kwargs)
        session.add(dns_record)
        session.flush()
        session.refresh(dns_record)
        return dns_record

    def __format__(self, format_spec):
        if format_spec != "a":
            return super(DnsRecord, self).__format__(format_spec)
        return self.fqdn


dns_record = DnsRecord.__table__  # pylint: disable-msg=C0103, E1101
dns_record.primary_key.name = '%s_pk' % _TN

# TODO: Remove this constraint
dns_record.append_constraint(
    UniqueConstraint('name', 'dns_domain_id', name='%s_name_domain_uk' % _TN))

# TODO: This is not quite correct
dns_record.info['unique_fields'] = ['name', 'dns_domain', 'dns_environment']
