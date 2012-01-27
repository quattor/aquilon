# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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
""" Mapping DNS domains to locations """

from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, String, Sequence, ForeignKey,
                        UniqueConstraint)
from sqlalchemy.orm import relation, backref, deferred
from sqlalchemy.ext.orderinglist import ordering_list

from aquilon.aqdb.model import Base, DnsDomain, Location

_TN = 'dns_map'


class DnsMap(Base):
    """
        Link dns domains to locations.

        It's kept as an association map to model the linkage, since it's not a
        good fit to model dns domains OR locations as one 'having' the other
        (i.e. a location may or may not HAVE a dns domain, nor do dns domains
        necessarily HAVE a location)
    """
    __tablename__ = _TN
    _class_label = "DNS Map"

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)

    location_id = Column(Integer, ForeignKey('location.id',
                                             name='%s_location_fk' % _TN,
                                             ondelete="CASCADE"),
                         nullable=False)

    dns_domain_id = Column(Integer, ForeignKey('dns_domain.id',
                                               name='%s_dns_domain_fk' % _TN),
                           nullable=False)

    # No default value to force the use of the Location.dns_maps relation to
    # manage the maps
    position = Column(Integer, nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = deferred(Column(String(255), nullable=True))

    location = relation(Location, lazy=False, innerjoin=True,
                        backref=backref('dns_maps', lazy=True,
                                        collection_class=ordering_list('position'),
                                        order_by=[position],
                                        cascade='all, delete-orphan'))

    dns_domain = relation(DnsDomain, lazy=False, innerjoin=True,
                          backref=backref('dns_maps', lazy=True, cascade='all'))

    def __repr__(self):
        return '<%s %s at %s>' % (self.__class__.__name__,
                                  self.dns_domain, self.location)

    def __init__(self, **kwargs):
        if 'position' in kwargs:  # pragma: no cover
            raise TypeError("Always use the Location.dns_maps relation to "
                            "manage the position attribute.")
        super(DnsMap, self).__init__(**kwargs)


dnsmap = DnsMap.__table__  # pylint: disable-msg=C0103, E1101
dnsmap.primary_key.name = '%s_pk' % _TN
dnsmap.info['unique_fields'] = ['location', 'dns_domain']

dnsmap.append_constraint(
    UniqueConstraint('location_id', 'dns_domain_id',
                     name='%s_loc_dns_dom_uk' % _TN))
# In theory we should have a unique constraint on (location_id, position), but
# the ordering_list documentation does not recommend it
