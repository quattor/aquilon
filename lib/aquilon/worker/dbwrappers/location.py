# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013,2014  Contributor
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
"""Wrapper to make getting a location simpler."""

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.orm import object_session

from aquilon.exceptions_ import NotFoundException, ArgumentError
from aquilon.aqdb.model import Location, DnsDomain
from aquilon.utils import validate_nlist_key


def get_location(session, query_options=None, compel=False, **kwargs):
    """Somewhat sophisticated getter for any of the location types."""
    cls = None
    name = None
    for key, mapper in Location.__mapper__.polymorphic_map.items():
        if key == "company":
            # temporary until locations in DB restructured
            value = kwargs.get("organization", None)
        else:
            value = kwargs.get(key, None)

        if value is None:
            continue

        if cls:  # pragma: no cover
            raise ArgumentError("Please specify just a single location "
                                "parameter.")
        name = value
        cls = mapper.class_

    if not cls:
        if compel:
            raise ArgumentError("Please specify a location parameter.")
        else:
            return None

    try:
        q = session.query(cls)
        q = q.filter_by(name=name)
        if query_options:
            q = q.options(query_options)
        dblocation = q.one()
    except NoResultFound:
        raise NotFoundException("%s %s not found." %
                                (cls._get_class_label(), name))
    except MultipleResultsFound:  # pragma: no cover
        raise ArgumentError("There are multiple matches for %s %s." %
                            (cls._get_class_label(), name))
    return dblocation


def add_location(session, cls, name, parent, **kwargs):
    validate_nlist_key(cls.__name__, name)
    cls.get_unique(session, name, preclude=True)
    dbloc = cls(name=name, parent=parent, **kwargs)
    session.add(dbloc)
    return dbloc


def get_default_dns_domain(dblocation):
    locations = dblocation.parents[:]
    locations.append(dblocation)
    locations.reverse()
    try:
        return next(loc.default_dns_domain
                    for loc in locations
                    if loc.default_dns_domain)
    except StopIteration:
        raise ArgumentError("There is no default DNS domain configured for "
                            "{0:l}.  Please specify --dns_domain."
                            .format(dblocation))


def update_location(dblocation, fullname=None, default_dns_domain=None,
                    comments=None):
    """ Update common location attributes """

    if fullname is not None:
        dblocation.fullname = fullname

    if default_dns_domain is not None:
        if default_dns_domain:
            session = object_session(dblocation)
            dbdns_domain = DnsDomain.get_unique(session, default_dns_domain,
                                                compel=True)
            dblocation.default_dns_domain = dbdns_domain
        else:
            dblocation.default_dns_domain = None

    if comments is not None:
        dblocation.comments = comments
