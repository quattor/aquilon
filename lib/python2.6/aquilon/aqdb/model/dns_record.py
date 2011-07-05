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
""" Representation of DNS Data """

from datetime import datetime
from collections import deque

from sqlalchemy import Integer, DateTime, Sequence, String, Column, ForeignKey

from sqlalchemy.orm import relation, deferred, backref, object_session
from sqlalchemy.ext.associationproxy import association_proxy

from aquilon.exceptions_ import NotFoundException, ArgumentError
from aquilon.aqdb.model import Base, Fqdn, DnsEnvironment
from aquilon.aqdb.model.dns_domain import parse_fqdn
from aquilon.aqdb.column_types import AqStr

_TN = "dns_record"

# This relation must be symmetric, i.e. whenever "x in _rr_conflict_map[y]" is
# True, "y in _rr_conflict_map[x]" must also be true.
_rr_conflict_map = {
    'a_record': frozenset(['alias', 'dynamic_stub', 'reserved_name',
                           'srv_record']),
    'alias': frozenset(['a_record', 'alias', 'dynamic_stub', 'reserved_name',
                        'srv_record']),
    'dynamic_stub': frozenset(['a_record', 'alias', 'dynamic_stub',
                               'reserved_name', 'srv_record']),
    'reserved_name': frozenset(['a_record', 'alias', 'dynamic_stub',
                                'reserved_name', 'srv_record']),
    'srv_record': frozenset(['alias', 'dynamic_stub', 'reserved_name',
                             'a_record']),
}


class DnsRecord(Base):
    """ Base class for a DNS Resource Record """

    __tablename__ = _TN
    _instance_label = 'fqdn'

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)

    fqdn_id = Column(Integer, ForeignKey('fqdn.id', name='%s_fqdn_fk' % _TN),
                     nullable=False)

    dns_record_type = Column(AqStr(32), nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    comments = deferred(Column('comments', String(255), nullable=True))

    fqdn = relation(Fqdn, lazy=False, innerjoin=True,
                    backref=backref('dns_records'))

    aliases = association_proxy('fqdn', 'aliases')
    srv_records = association_proxy('fqdn', 'srv_records')

    __mapper_args__ = {'polymorphic_on': dns_record_type,
                       'polymorphic_identity': 'dns_record'}

    @classmethod
    def get_unique(cls, session, fqdn=None, name=None, dns_domain=None,
                   dns_environment=None, compel=False, preclude=False, **kwargs):
        # Proxy FQDN lookup to the Fqdn class
        if not fqdn or not isinstance(fqdn, Fqdn):
            if not isinstance(dns_environment, DnsEnvironment):
                dns_environment = DnsEnvironment.get_unique_or_default(session,
                                                                      dns_environment)
            if fqdn:
                if name or dns_domain:
                    raise TypeError("fqdn and name/dns_domain cannot be mixed")
                (name, dns_domain) = parse_fqdn(session, fqdn)
            try:
                # Do not pass preclude=True to Fqdn
                fqdn = Fqdn.get_unique(session, name=name,
                                       dns_domain=dns_domain,
                                       dns_environment=dns_environment,
                                       compel=compel)
            except NotFoundException:
                # Replace the "Fqdn ... not found" message with a more user
                # friendly one
                msg = "%s %s.%s, %s not found." % (cls._get_class_label(),
                                                   name, dns_domain,
                                                   format(dns_environment, "l"))
                raise NotFoundException(msg)
            if not fqdn:
                return None

        return super(DnsRecord, cls).get_unique(session, fqdn=fqdn,
                                                compel=compel,
                                                preclude=preclude, **kwargs)

    @classmethod
    def get_or_create(cls, session, **kwargs):
        dns_record = cls.get_unique(session, **kwargs)
        if dns_record:
            return dns_record

        dns_record = cls(**kwargs)
        session.add(dns_record)
        session.flush()
        return dns_record

    def __format__(self, format_spec):
        if format_spec != "a":
            return super(DnsRecord, self).__format__(format_spec)
        return str(self.fqdn)

    @property
    def all_aliases(self):
        """ Returns all distinct aliases that point to this record

            If Alias1 -> B, A2lias2 -> B, B -> C, remove duplicates.
        """

        found = {}
        queue = deque(self.aliases)
        while queue:
            alias = queue.popleft()
            found[str(alias.fqdn)] = alias
            for a in alias.aliases:
                if not str(a.fqdn) in found:
                    queue.append(a)

        # Ensure a deterministic order of the returned values
        aliases = found.values()
        aliases.sort(cmp=lambda x, y: cmp(str(x.fqdn), str(y.fqdn)))
        return aliases

    def __init__(self, fqdn=None, **kwargs):
        if not fqdn:
            raise ValueError("fqdn cannot be empty")
        session = object_session(fqdn)
        if not session:
            raise ValueError("fqdn must be already part of a session")

        # Disable autoflush temporarily
        flush_state = session.autoflush
        session.autoflush = False

        # self.dns_record_type is not populated by the ORM yet, so query our
        # class
        own_type = self.__class__.__mapper_args__['polymorphic_identity']

        # Asking for just one column makes both the query and the ORM faster
        q = session.query(DnsRecord.dns_record_type).filter_by(fqdn=fqdn)
        for existing in q.all():
            if existing.dns_record_type in _rr_conflict_map[own_type]:
                cls = DnsRecord.__mapper__.polymorphic_map[existing.dns_record_type].class_
                raise ArgumentError("%s %s already exist." %
                                    (cls._get_class_label(), fqdn))

        session.autoflush = flush_state
        super(DnsRecord, self).__init__(fqdn=fqdn, **kwargs)


dns_record = DnsRecord.__table__  # pylint: disable=C0103, E1101
dns_record.primary_key.name = '%s_pk' % _TN

dns_record.info['unique_fields'] = ['fqdn']
