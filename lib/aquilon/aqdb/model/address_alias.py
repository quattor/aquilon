# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015,2019  Contributor
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
""" DNS Address Alias records """

from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relation, backref, column_property, object_session
from sqlalchemy.sql import select, func

from aquilon.exceptions_ import AquilonError, ArgumentError
from aquilon.aqdb.model import DnsRecord, Fqdn, ARecord, DnsRecordTargetMixin

_TN = 'address_alias'


class AddressAlias(DnsRecordTargetMixin, DnsRecord):
    """ DNS alias of A-record(s) """
    __tablename__ = _TN
    _class_label = "Address Alias"

    dns_record_id = Column(ForeignKey(DnsRecord.id, ondelete='CASCADE'),
                           primary_key=True)

    target_id = Column(ForeignKey(Fqdn.id, name='%s_target_fk' % _TN),
                       nullable=False, index=True)

    target = relation(Fqdn, innerjoin=True, foreign_keys=target_id,
                      backref=backref('address_aliases'))

    __table_args__ = ({'info': {'unique_fields': ['fqdn'],
                                'extra_search_fields': ['target',
                                                        'dns_environment']}},)
    __mapper_args__ = {'polymorphic_identity': _TN}

    @property
    def target_ip(self):
        # AddressAlias only allows reference to ARecord which only contain
        # one ip address per name.
        return self.target.dns_records[0].ip

    @property
    def target_network(self):
        # Same as for target_ip
        return self.target.dns_records[0].network

    def __init__(self, fqdn, target, **kwargs):
        if not isinstance(fqdn, Fqdn):  # pragma: no cover
            raise TypeError("The fqdn of an %s record must be an Fqdn." %
                            (AddressAlias._get_class_label()))

        if not isinstance(target, Fqdn):  # pragma: no cover
            raise TypeError("The target of an %s record must be an Fqdn." %
                            (AddressAlias._get_class_label()))

        session = object_session(target)
        if not session:  # pragma: no cover
            raise AquilonError("The target name must already be part of "
                               "the session.")

        for rr in target.dns_records:
            if isinstance(rr, ARecord):
                break
        else:
            raise ArgumentError("The target of each %s record must resolve to "
                                "one and only one ip address." %
                                (AddressAlias._get_class_label()))

        # Disable autoflush because self is not ready to be pushed to
        # the DB yet
        with session.no_autoflush:
            # Do not allow two records pointing at the same target
            for rr in fqdn.dns_records:
                if isinstance(rr, AddressAlias) and rr.target == target:
                    raise ArgumentError("{0} with target {1} already exists."
                                        .format(rr, target.fqdn))

        self.target = target

        super(AddressAlias, self).__init__(fqdn=fqdn, **kwargs)

# Most addresses will not have aliases. This bulk loadable property allows the
# formatter to avoid querying the alias table for every displayed DNS record
# See http://www.sqlalchemy.org/trac/ticket/2139 about why we need the .alias()
DnsRecord.address_alias_cnt = column_property(
    select([func.count()], DnsRecord.fqdn_id == AddressAlias.__table__.alias().c.target_id)
    .label("address_alias_cnt"), deferred=True)
