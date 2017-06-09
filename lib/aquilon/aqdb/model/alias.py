# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2011,2012,2013,2014,2015,2017  Contributor
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
""" DNS CNAME records """

from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relation, backref, column_property
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.sql import select, func

from aquilon.aqdb.model import DnsRecord, Fqdn, DnsRecordTargetMixin

_TN = 'alias'


class Alias(DnsRecordTargetMixin, DnsRecord):
    """ Aliases a.k.a. CNAMES """
    __tablename__ = _TN
    MAX_ALIAS_DEPTH = 4

    dns_record_id = Column(ForeignKey(DnsRecord.id, ondelete='CASCADE'),
                           primary_key=True)

    target_id = Column(ForeignKey(Fqdn.id, name='%s_target_fk' % _TN),
                       nullable=False, index=True)

    target = relation(Fqdn, innerjoin=True, foreign_keys=target_id,
                      backref=backref('aliases'))

    # The same name may resolve to multiple RRs
    target_rrs = association_proxy('target', 'dns_records')

    __table_args__ = ({'info': {'unique_fields': ['fqdn'],
                                'extra_search_fields': ['target',
                                                        'dns_environment']}},)
    __mapper_args__ = {'polymorphic_identity': _TN}

    @property
    def alias_depth(self):
        depth = 0
        for tgt in self.target_rrs:
            if not isinstance(tgt, Alias):
                continue
            depth = max(depth, tgt.alias_depth)
        return depth + 1

    def get_alias_targets(self):
        tlist = [self.target.fqdn]
        for tgt in self.target_rrs:
            if not isinstance(tgt, Alias):
                continue
            # this may end up with duplicates (ignore)
            tlist.extend(tgt.get_alias_targets())
        return tlist

    def __init__(self, fqdn, target, **kwargs):
        self.target = target
        super(Alias, self).__init__(fqdn=fqdn, **kwargs)
        if self.alias_depth > self.MAX_ALIAS_DEPTH:
            raise ValueError("Maximum alias depth exceeded")

# Most addresses will not have aliases. This bulk loadable property allows the
# formatter to avoid querying the alias table for every displayed DNS record
# See http://www.sqlalchemy.org/trac/ticket/2139 about why we need the .alias()
DnsRecord.alias_cnt = column_property(
    select([func.count()], DnsRecord.fqdn_id == Alias.__table__.alias().c.target_id)
    .label("alias_cnt"), deferred=True)
