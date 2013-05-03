# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
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

from sqlalchemy.orm import relation, deferred, backref, object_session, lazyload
from sqlalchemy.orm.attributes import set_committed_value
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

    comments = deferred(Column(String(255), nullable=True))

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

        result = super(DnsRecord, cls).get_unique(session, fqdn=fqdn,
                                                  compel=compel,
                                                  preclude=preclude, **kwargs)
        if result:
            # Make sure not to load the relation again if we already know its
            # value
            set_committed_value(result, 'fqdn', fqdn)
        return result

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
                if existing.dns_record_type in _rr_conflict_map[own_type]:
                    raise ArgumentError("{0} already exist.".format(existing))

        super(DnsRecord, self).__init__(fqdn=fqdn, **kwargs)

dns_record = DnsRecord.__table__  # pylint: disable=C0103
dns_record.info['unique_fields'] = ['fqdn']
dns_record.info['extra_search_fields'] = ['dns_environment']
