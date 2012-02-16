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
""" DNS CNAME records """

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relation, backref, column_property
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.sql import select, func

from aquilon.aqdb.model import DnsRecord, Fqdn

_TN = 'alias'
MAX_ALIAS_DEPTH = 4


class Alias(DnsRecord):
    """ Aliases a.k.a. CNAMES """
    __tablename__ = _TN

    dns_record_id = Column(Integer, ForeignKey('dns_record.id',
                                               name='%s_dns_record_fk' % _TN,
                                               ondelete='CASCADE'),
                           primary_key=True)

    target_id = Column(Integer, ForeignKey('fqdn.id',
                                           name='%s_target_fk' % _TN),
                       nullable=False)

    target = relation(Fqdn, lazy=True,
                      primaryjoin=target_id == Fqdn.id,
                      backref=backref('aliases', lazy=True))

    # The same name may resolve to multiple RRs
    target_rrs = association_proxy('target', 'dns_records')

    __mapper_args__ = {'polymorphic_identity': _TN}

    @property
    def alias_depth(self):
        depth = 0
        for tgt in self.target_rrs:
            if not isinstance(tgt, Alias):
                continue
            depth = max(depth, tgt.alias_depth)
        return depth + 1

    def __init__(self, **kwargs):
        super(Alias, self).__init__(**kwargs)
        if self.alias_depth > MAX_ALIAS_DEPTH:
            raise ValueError("Maximum alias depth exceeded")


alias = Alias.__table__  # pylint: disable=C0103, E1101
alias.primary_key.name = '%s_pk' % _TN
alias.info['unique_fields'] = ['fqdn']
alias.info['extra_search_fields'] = ['target']

# Most addresses will not have aliases. This bulk loadable property allows the
# formatter to avoid querying the alias table for every displayed DNS record
# See http://www.sqlalchemy.org/trac/ticket/2139 about why we need the .alias()
DnsRecord.alias_cnt = column_property(
    select([func.count()], DnsRecord.fqdn_id == alias.alias().c.target_id)
    .label("alias_cnt"), deferred=True)
