# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013,2014,2016,2017,2018  Contributor
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
    return get_locations(session, query_options=query_options, compel=compel,
                         separator=False, single_location=True, **kwargs)


def get_location_list(session, compel=False, **kwargs):
    """
    A variant of get_location(), accepting multiple, comma-separated names
    """
    return get_locations(session, compel=compel, multiple_types=False,
                         separator=',', single_location=False,
                         unique_values=False, **kwargs)


def get_locations(session, query_options=None, compel=False,
                  locfunc=None, multiple_types=True, separator=None,
                  unique_values=True, single_location=False, **kwargs):
    """Somewhat sophisticated getter for any of the location types.

    This allows to have multiple values for the locations, it accepts repeated
    arguments (if the location argument is a list for instance) and
    char-separated arguments.

    query_options:
        options to pass to the get_unique call
    compel:
        whether or not to force a location to be returned or raise an error
    locfunc:
        the function used to compute the location name in the kwargs
        (default: only uses the location type name)
    multiple_types:
        whether or not multiple locations are authorized; when enabled, this
        will authorize multiple location types at the same time
    separator:
        the char (or chars) that separates the locations
        (default: disabled if single_location, comma else, e.g. --hub ny,hk ;
         set to False to explicitly disable, or any value to explicitly enable)
    unique_values:
        whether or not to discard the repetitions of location values
        (i.e. --city ln,ln to only one 'ln' occurrence) (default: True)
    single_location:
        whether or not there should only be one location found in the call
        of that function (default: False)
    """
    if not locfunc:
        def locfunc(loc):
            return loc

    if separator is None:
        separator = False if single_location else ','

    # Extract location-specific options from kwargs
    location_args = {}
    for key, mapper in Location.__mapper__.polymorphic_map.items():
        if kwargs.get(locfunc(key)) is not None:
            # If the data is not a list, put it in a form of one
            values = kwargs[locfunc(key)]
            if not isinstance(values, list):
                values = [values, ]

            # If a separator is specified, split the values
            if separator:
                split_values = []
                for v in values:
                    split_values.extend(v.split(separator))
                values = split_values

            # Update the location args with these locations information
            locinfo = location_args.setdefault(key, {})
            locinfo['class'] = mapper.class_
            locinfo.setdefault('values', []).extend(values)

    # If we did not find any location, either raise an exception (compel)
    # or return None (single_location) or an empty list.
    if not location_args:
        if compel:
            raise ArgumentError("Please specify a location parameter.")
        return None if single_location else []
    elif single_location and (
            len(location_args) > 1 or
            len(location_args.itervalues().next()['values']) > 1):
        raise ArgumentError("Please specify just a single location "
                            "parameter.")

    locations = []
    for locinfo in location_args.itervalues():
        cls = locinfo['class']
        values = locinfo['values']

        # If we only want unique values, put the values in form of a set
        if unique_values:
            values = set(values)

        for name in values:
            locations.append(cls.get_unique(session, name,
                                            query_options=query_options,
                                            compel=True))

    if single_location:
        locations = locations[0]
    return locations


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
    # To Do: move this to Building model @validates method so that different
    # location models can have different validate_uri methods
    # Additional attributes - logger, force, can be passed via init
    # or added to class instance directly in render
    config = Config()
    location_feed = None
    validator = config.lookup_tool("location_uri_validator")
    if config.has_value("location_feeds", clsname + "_feed"):
        location_feed = config.get("location_feeds", clsname + "_feed")
    if force is None and \
                    validator is not None and \
                    location_feed is not None:
        try:
            run_command([validator, "--uri", uri, "--location-type", clsname,
                        "--location", name, "--location-feed", location_feed],
                        logger=logger, stream_level=CLIENT_INFO)
        except ProcessException as err:
            raise ArgumentError("Location URI not valid: %s%s" % (err.out, err.err))

    return uri

def update_location(dblocation, fullname=None, default_dns_domain=None,
                    comments=None, uri=None, force_uri=None, logger=None,
                    netdev_require_rack=None, next_rackid=None):
    """ Update common location attributes """

    if fullname is not None:
        dblocation.fullname = fullname

    if next_rackid is not None:
        dblocation.next_rackid = next_rackid

    if uri is not None:
        dblocation.uri = validate_uri(uri, dblocation.__class__.__name__,
                                      dblocation.name, force_uri, logger)

    if netdev_require_rack is not None:
        dblocation.netdev_rack = netdev_require_rack

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
