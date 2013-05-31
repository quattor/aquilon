# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013  Contributor
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
""" NS Records tell us what name servers to use for a given Dns Domain """
from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, String, ForeignKey,
                        PrimaryKeyConstraint)
from sqlalchemy.orm import relation, backref, deferred

from aquilon.aqdb.model import Base, DnsDomain, ARecord

_TN = 'ns_record'


class NsRecord(Base):
    """ NS Records tell us what name servers to use for a given Dns Domain """
    __tablename__ = _TN
    _class_label = "Name Server"

    a_record_id = Column(Integer, ForeignKey(ARecord.dns_record_id,
                                             name='%s_a_record_fk' % (_TN)),
                         nullable=False)

    dns_domain_id = Column(Integer, ForeignKey('dns_domain.id',
                                               name='%s_domain_fk' % (_TN)),
                           nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    comments = deferred(Column(String(255), nullable=True))

    a_record = relation(ARecord, lazy=False, innerjoin=True,
                        backref=backref('_ns_records', cascade='all',
                                        passive_deletes=True))

    dns_domain = relation(DnsDomain, lazy=False, innerjoin=True,
                          backref=backref('_ns_records', cascade='all'))

    __table_args__ = (PrimaryKeyConstraint(a_record_id, dns_domain_id,
                                           name="%s_pk" % _TN),)

    def __format__(self, format_spec):
        instance = "%s [%s] of DNS Domain %s" % (self.a_record.fqdn,
                                                 self.a_record.ip,
                                                 self.dns_domain.name)
        return self.format_helper(format_spec, instance)

    def __repr__(self):
        msg = '<%s dns_domain=%s %s>' % (self.__class__.__name__,
                                         self.dns_domain.name,
                                         self.a_record.fqdn)
        return msg

    def _get_instance_label(self):
        return "{0:a} of {1:l}".format(self.a_record, self.dns_domain)

nsrecord = NsRecord.__table__  # pylint: disable=C0103
nsrecord.info['unique_fields'] = ['a_record', 'dns_domain']

# Association proxies from/to NSRecord:
# DnsDomain.servers = association_proxy('_name_servers', 'a_record')

#TODO: proxy all IP addresses through to DnsDomains when System is removed
