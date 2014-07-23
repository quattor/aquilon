# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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

    location_id = Column(Integer, ForeignKey(Location.id,
                                             name='%s_location_fk' % _TN,
                                             ondelete="CASCADE"),
                         nullable=False)

    dns_domain_id = Column(Integer, ForeignKey(DnsDomain.id,
                                               name='%s_dns_domain_fk' % _TN),
                           nullable=False)

    # No default value to force the use of the Location.dns_maps relation to
    # manage the maps
    position = Column(Integer, nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = deferred(Column(String(255), nullable=True))

    location = relation(Location, lazy=False, innerjoin=True,
                        backref=backref('dns_maps',
                                        collection_class=ordering_list('position'),
                                        order_by=[position],
                                        cascade='all, delete-orphan'))

    dns_domain = relation(DnsDomain, lazy=False, innerjoin=True,
                          backref=backref('dns_maps', cascade='all'))

    # In theory we should have a unique constraint on (location_id, position),
    # but the ordering_list documentation does not recommend that
    __table_args__ = (UniqueConstraint(location_id, dns_domain_id,
                                       name='%s_loc_dns_dom_uk' % _TN),)

    def __repr__(self):
        return '<%s %s at %s>' % (self.__class__.__name__,
                                  self.dns_domain, self.location)

    def __init__(self, **kwargs):
        if 'position' in kwargs:  # pragma: no cover
            raise TypeError("Always use the Location.dns_maps relation to "
                            "manage the position attribute.")
        super(DnsMap, self).__init__(**kwargs)

dnsmap = DnsMap.__table__  # pylint: disable=C0103
dnsmap.info['unique_fields'] = ['location', 'dns_domain']
