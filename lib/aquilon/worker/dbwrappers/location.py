# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013,2014,2016,2017  Contributor
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

from sqlalchemy.orm import object_session

from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.aqdb.model import Location, DnsDomain
from aquilon.utils import validate_nlist_key
from aquilon.config import Config
from aquilon.worker.processes import run_command
from aquilon.worker.logger import CLIENT_INFO

def get_location(session, query_options=None, compel=False, **kwargs):
    """Somewhat sophisticated getter for any of the location types."""
    # Extract location-specific options from kwargs
    location_args = {key: (mapper.class_, kwargs.get(key))
                     for key, mapper in Location.__mapper__.polymorphic_map.items()
                     if key in kwargs and kwargs[key] is not None}
    if len(location_args) > 1:
        raise ArgumentError("Please specify just a single location "
                            "parameter.")
    if not location_args:
        if compel:
            raise ArgumentError("Please specify a location parameter.")
        return None

    _, (cls, name) = location_args.popitem()
    return cls.get_unique(session, name, query_options=query_options,
                          compel=True)


def get_location_list(session, compel=False, **kwargs):
    """
    A variant of get_location(), accepting multiple, comma-separated names
    """
    location_args = {key: (mapper.class_, kwargs.get(key))
                     for key, mapper in Location.__mapper__.polymorphic_map.items()
                     if key in kwargs and kwargs[key] is not None}
    if len(location_args) > 1:
        raise ArgumentError("Please specify just a single location "
                            "parameter.")
    if not location_args:
        if compel:
            raise ArgumentError("Please specify a location parameter.")
        return []

    _, (cls, names) = location_args.popitem()
    return [cls.get_unique(session, name.strip(), compel=True)
            for name in names.split(",")]


def add_location(session, cls, name, parent, force_uri=None, logger=None, **kwargs):
    validate_nlist_key(cls.__name__, name)
    if 'uri' in kwargs and kwargs['uri'] is not None:
        validate_uri(kwargs['uri'], cls.__name__, name, force_uri, logger)

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

def validate_uri(uri, clsname, name, force, logger):
    config = Config()
    validator = config.lookup_tool("location_uri_validator")
    if config.has_section("location_feeds"):
        location_feed = config.get("location_feeds", clsname + "_feed")

    if force is None and validator is not None:
        try:
            run_command([validator, "--uri", uri, "--location-type", clsname,
                        "--location", name, "--location-feed", location_feed],
                        logger=logger, stream_level=CLIENT_INFO)
        except ProcessException as err:
            raise ArgumentError("Location URI not valid: %s%s" % (err.out, err.err))

    return uri

def update_location(dblocation, fullname=None, default_dns_domain=None,
                    comments=None, uri=None, force_uri=None, logger=None,
                    next_rackid=None):
    """ Update common location attributes """

    if fullname is not None:
        dblocation.fullname = fullname

    if next_rackid is not None:
        dblocation.next_rackid = next_rackid

    if uri is not None:
        dblocation.uri = validate_uri(uri, dblocation.__class__.__name__,
                                      dblocation.name, force_uri, logger)

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
