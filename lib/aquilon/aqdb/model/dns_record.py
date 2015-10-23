# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013,2014,2015  Contributor
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
""" Representation of DNS Data """

from datetime import datetime
from collections import deque

from sqlalchemy import Integer, DateTime, Sequence, String, Column, ForeignKey
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import (relation, deferred, backref, object_session,
                            lazyload, validates)
from sqlalchemy.ext.associationproxy import association_proxy

from aquilon.exceptions_ import NotFoundException, ArgumentError
from aquilon.aqdb.model import Base, Fqdn, DnsEnvironment, Grn
from aquilon.aqdb.model.dns_domain import parse_fqdn
from aquilon.aqdb.column_types import AqStr

_TN = "dns_record"

# This relation must be symmetric, i.e. whenever "x in _rr_conflict_map[y]" is
# True, "y in _rr_conflict_map[x]" must also be true.
_rr_conflict_map = {
    'a_record': frozenset(['alias', 'dynamic_stub', 'reserved_name',
                           'address_alias',
                           'srv_record']),
    'address_alias': frozenset(['a_record', 'alias', 'dynamic_stub',
                                'reserved_name']),
    'alias': frozenset(['a_record', 'alias', 'dynamic_stub', 'reserved_name',
                        'address_alias',
                        'srv_record']),
    'dynamic_stub': frozenset(['a_record', 'alias', 'dynamic_stub',
                               'address_alias',
                               'reserved_name', 'srv_record']),
    'reserved_name': frozenset(['a_record', 'alias', 'dynamic_stub',
                                'address_alias',
                                'reserved_name', 'srv_record']),
    'srv_record': frozenset(['alias', 'dynamic_stub', 'reserved_name',
                             'a_record']),
}


class DnsRecord(Base):
    """ Base class for a DNS Resource Record """

    __tablename__ = _TN
    _instance_label = 'fqdn'

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)

    fqdn_id = Column(ForeignKey(Fqdn.id), nullable=False, index=True)

    dns_record_type = Column(AqStr(32), nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    comments = deferred(Column(String(255), nullable=True))

    ttl = Column(Integer, nullable=True)

    owner_eon_id = Column(ForeignKey(Grn.eon_id, name='%s_owner_grn_fk' % _TN),
                          nullable=True)

    fqdn = relation(Fqdn, lazy=False, innerjoin=True,
                    backref=backref('dns_records'))

    owner_grn = relation(Grn)

    aliases = association_proxy('fqdn', 'aliases')
    srv_records = association_proxy('fqdn', 'srv_records')
    address_aliases = association_proxy('fqdn', 'address_aliases')

    __table_args__ = ({'info': {'unique_fields': ['fqdn'],
                                'extra_search_fields': ['dns_environment']}},)
    __mapper_args__ = {'polymorphic_on': dns_record_type,
                       'polymorphic_identity': _TN}

    @classmethod
    def get_unique(cls, session, fqdn=None, name=None, dns_domain=None,
                   dns_environment=None, compel=False, preclude=False, **kwargs):
        # Proxy FQDN lookup to the Fqdn class
        if not fqdn or not isinstance(fqdn, Fqdn):
            if not isinstance(dns_environment, DnsEnvironment):
                dns_environment = DnsEnvironment.get_unique_or_default(session,
                                                                       dns_environment)
            if fqdn:
                if name or dns_domain:  # pragma: no cover
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

        # We already have the FQDN, no need to load it again
        if "query_options" not in kwargs:
            kwargs["query_options"] = [lazyload("fqdn")]

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

    @validates('ttl')
    def validate_ttl(self, key, value):
        if value is not None:
            value = int(value)
            if value < 0 or value > 2147483647:
                # Valid ttl range according to RFC 2181
                raise ArgumentError("TTL must be between 0 and 2147483647.")

        return value

    @validates('owner_grn')
    def validate_grn(self, key, grn):
        if grn:
            session = object_session(self)
            with session.no_autoflush:
                self.check_grn_conflict(grn)

        return grn

    def check_grn_conflict(self, grn):
        if self.hardware_entity:
            raise ArgumentError("{0} is a primary name. GRN should not be set "
                                "but derived from the device.".format(self))

        if getattr(self, 'assignments', None):
            ifaces = ", ".join(sorted(addr.interface.qualified_name
                                    for addr in self.assignments))
            raise ArgumentError("{0} is already be used by the interfaces "
                                "{1!s}. GRN should not be set but derived "
                                "from the device.".format(self, ifaces))

    @property
    def dependent_grn(self):
        """ Returns the first GRN found set to this DnsRecord
            or its parents
        """
        if self.owner_grn:
            return self.owner_grn

        for attr in ('aliases', 'srv_records', 'address_aliases'):
            records = getattr(self, attr, None)
            if records:
                for rec in records:
                    grn = rec.dependent_grn
                    if grn:
                        return grn

        return None

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
        return sorted(found.values(), key=lambda x: str(x.fqdn))

    @property
    def all_address_aliases(self):
        # Ensure a deterministic order of all address aliases
        return sorted(self.address_aliases, key=lambda x: str(x.fqdn))

    @property
    def is_unused(self):
        # TODO: This property is intended for ARecord's where we are
        # guarding delete_dns_record.  At the moment we assume that
        # a record is used.  We should probably check all_aliases.
        return False

    def __init__(self, fqdn=None, **kwargs):
        if not fqdn:  # pragma: no cover
            raise ValueError("fqdn cannot be empty")
        session = object_session(fqdn)
        if not session:  # pragma: no cover
            raise ValueError("fqdn must be already part of a session")

        # Disable autoflush because self is not ready to be pushed to the DB yet
        with session.no_autoflush:
            # self.dns_record_type is not populated by the ORM yet, so query our
            # class
            own_type = self.__class__.__mapper_args__['polymorphic_identity']

            # Asking for just one column makes both the query and the ORM faster
            for existing in fqdn.dns_records:
                # Do not bother checking records which are scheduled to be
                # deleted
                if existing in session.deleted or inspect(existing).deleted:
                    continue
                if existing.dns_record_type in _rr_conflict_map[own_type]:
                    raise ArgumentError("{0} already exist.".format(existing))

        self.fqdn = fqdn

        super(DnsRecord, self).__init__(**kwargs)
