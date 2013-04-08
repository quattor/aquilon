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
""" DNS SRV records """

import re

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relation, backref, object_session, validates
from sqlalchemy.ext.associationproxy import association_proxy

from aquilon.exceptions_ import AquilonError, ArgumentError
from aquilon.aqdb.model import DnsRecord, Fqdn, ARecord, Alias

_TN = 'srv_record'
_name_re = re.compile(r'_([^_.]+)\._([^_.]+)$')

PROTOCOLS = ['tcp', 'udp']


class SrvRecord(DnsRecord):
    __tablename__ = _TN
    _class_label = "SRV Record"

    dns_record_id = Column(Integer, ForeignKey('dns_record.id',
                                               name='%s_dns_record_fk' % _TN,
                                               ondelete='CASCADE'),
                           primary_key=True)

    priority = Column(Integer, nullable=False)
    weight = Column(Integer, nullable=False)
    port = Column(Integer, nullable=False)

    target_id = Column(Integer, ForeignKey('fqdn.id',
                                           name='%s_target_fk' % _TN),
                       nullable=False)

    target = relation(Fqdn, foreign_keys=target_id,
                      backref=backref('srv_records'))

    target_rrs = association_proxy('target', 'dns_records')

    __mapper_args__ = {'polymorphic_identity': _TN}

    @validates('priority', 'weight', 'port')
    def validate_ushort(self, key, value):
        value = int(value)
        if key == 'port':
            min = 1
        else:
            min = 0
        if value < min or value > 65535:
            raise ArgumentError("The %s must be between %d and 65535." %
                                (key, min))
        return value

    @property
    def service(self):
        m = _name_re.match(self.fqdn.name)
        if not m:  # pragma: no cover
            raise AquilonError("Malformed SRV FQDN in AQDB: %s" % self.fqdn)
        return m.group(1)

    @property
    def protocol(self):
        m = _name_re.match(self.fqdn.name)
        if not m:  # pragma: no cover
            raise AquilonError("Malformed SRV FQDN in AQDB: %s" % self.fqdn)
        return m.group(2)

    def __init__(self, service, protocol, dns_domain, dns_environment, priority,
                 weight, port, target, **kwargs):
        if not isinstance(target, Fqdn):  # pragma: no cover
            raise TypeError("The target of an SRV record must be an Fqdn.")
        session = object_session(target)
        if not session:  # pragma: no cover
            raise AquilonError("The target name must already be part of "
                               "the session.")
        # SRV records are special, as the FQDN is managed internally
        if "fqdn" in kwargs:  # pragma: no cover
            raise AquilonError("SRV records do not accept an FQDN argument.")

        self.validate_ushort('priority', priority)
        self.validate_ushort('weight', weight)
        self.validate_ushort('port', port)

        # RFC 2782:
        # - there must be one or more address records for the target
        # - the target must not be an alias
        found_address = False
        for rr in target.dns_records:
            if isinstance(rr, ARecord):
                found_address = True
            elif isinstance(rr, Alias):
                raise ArgumentError("The target of an SRV record must not be "
                                    "an alias.")
        if not found_address:
            raise ArgumentError("The target of an SRV record must resolve to "
                                "one or more addresses.")

        if protocol not in PROTOCOLS:
            raise ArgumentError("Unknown protocol %s." % protocol)
        name = "_%s._%s" % (service.strip().lower(), protocol.strip().lower())

        # Disable autoflush because self is not ready to be pushed to the DB yet
        with session.no_autoflush:
            fqdn = Fqdn.get_or_create(session, name=name, dns_domain=dns_domain,
                                      dns_environment=dns_environment,
                                      ignore_name_check=True)

            # Do not allow two SRV records pointing at the same target
            for rr in fqdn.dns_records:
                if isinstance(rr, SrvRecord) and rr.target == target and \
                   rr.protocol == protocol and rr.service == service:
                    raise ArgumentError("{0} already exists.".format(rr))

        super(SrvRecord, self).__init__(fqdn=fqdn, priority=priority, weight=weight,
                                        port=port, target=target, **kwargs)


srv_record = SrvRecord.__table__  # pylint: disable=C0103
srv_record.primary_key.name = '%s_pk' % _TN
srv_record.info["unique_fields"] = ["fqdn"]
srv_record.info["extra_search_fields"] = ['target', 'dns_environment']
