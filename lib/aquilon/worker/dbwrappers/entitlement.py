# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2018  Contributor
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
"""Wrappers for the entitlement tables."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import (
    Archetype,
    Cluster,
    Entitlement,
    EntitlementType,
    Grn,
    HostEnvironment,
    Personality,
    User,
)
from aquilon.worker.dbwrappers.grn import lookup_grn
from aquilon.worker.dbwrappers.host import hostname_to_host
from aquilon.worker.dbwrappers.location import get_locations

from sqlalchemy import (
    and_,
    or_,
)
from sqlalchemy.orm.session import object_session


def get_entitlement_classes(on=None, to=None):
    if on and not isinstance(on, list):
        on = [on, ]
    if to and not isinstance(to, list):
        to = [to, ]

    return [
        cls
        for cls in Entitlement.__subclasses__()
        if hasattr(cls, '_to_class') and hasattr(cls, '_on_class') and
        (to is None or
         any(t == cls._to_class or isinstance(t, cls._to_class)
             for t in to)) and
        (on is None or
         any(o == cls._on_class or isinstance(o, cls._on_class)
             for o in on))
    ]


def get_entitlement_class_for(on, to):
    classes = get_entitlement_classes(on, to)
    if len(classes) > 1:
        raise RuntimeError('More than one matching class for '
                           'onects {} and {}.'.format(on, to))
    elif not classes:
        raise RuntimeError('No matching class found for onects '
                           '{} and {}'.format(on, to))
    return classes[0]


def get_entitlements_options(session, logger, config, type=None,
                             on_host_environment=None,
                             on_single=False, on_single_type=False,
                             requires_type=False,
                             **arguments):
    # Check if the entitlement type provided is valid
    if requires_type or type:
        dbtype = EntitlementType.get_unique(session, name=type, compel=True)
    else:
        dbtype = None

    def to_list(param):
        if not param:
            return []
        elif not isinstance(param, list):
            return [param, ]
        return param

    # Prepare the information to parse and convert to objects the
    # users/grns owning the entitlements; this cannot be done
    # out of the function as we use some of the function parameters to
    # define the lambda functions.
    # name = name of the parameter (used to check the command line)
    # func = function to received one parameter and return an object
    #        of the type expected for the parameter
    to_params = [
        {
            'name': 'grn',
            'func': lambda v: lookup_grn(session, v, None, logger=logger,
                                         config=config),
        },
        {
            'name': 'eon_id',
            'func': lambda v: lookup_grn(session, None, v, logger=logger,
                                         config=config),
        },
        {
            'name': 'user',
            'func': lambda v: User.get_unique(session, name=v, compel=True),
        },
    ]

    # Prepare the setup to parse and convert to objects the host/cluster/...
    # on which the entitlements are
    on_params = [
        {
            'name': 'hostname',
            'func': lambda v: hostname_to_host(session, v),
        },
        {
            'name': 'cluster',
            'func': lambda v: Cluster.get_unique(session, v, compel=True),
        },
        {
            'name': 'personality',
            'func': lambda v: Personality.get_unique(session, name=v,
                                                     compel=True),
        },
        {
            'name': 'archetype',
            'func': lambda v: Archetype.get_unique(session, v, compel=True),
        },
        {
            'name': 'grn',
            'func': lambda v: lookup_grn(session, v, None, logger=logger,
                                         config=config),
        },
        {
            'name': 'eon_id',
            'func': lambda v: lookup_grn(session, None, v, logger=logger,
                                         config=config),
        },
    ]

    # Go through the received parameters to identify all the objects required
    dbobjs = {}
    for obj, params in (('to', to_params), ('on', on_params)):
        dbobjs[obj] = []
        for param in params:
            name = param['name']
            func = param['func']

            paramarg = arguments.get('{}_{}'.format(obj, name))
            paramarg_list = arguments.get('{}_list'.format(paramarg))

            if paramarg or paramarg_list:
                paramarg_list = paramarg_list or []
                for v in to_list(paramarg) + paramarg_list:
                    dbobjs[obj].append(func(v))

    # Put back the dbobjs into named variables
    dbtos = dbobjs.pop('to', [])
    dbons = dbobjs.pop('on', [])

    # If the function was called to return a single object
    if on_single:
        if not dbons:
            dbons = None
        elif len(dbons) > 1:
            raise ArgumentError('More than a single object provided.')
        else:
            dbons = dbons[0]
    elif on_single_type and len({o.__class__ for o in dbons}) > 1:
        raise ArgumentError('More than a single object type provided.')

    # Try to determine the location; if a location is found for an object
    # that does not require it, it will fail while trying to update the
    # entitlements, so we do not need to perform any check here (even more
    # so that the aq client command should already have performed that
    # check).
    dblocations = get_locations(session,
                                locfunc=lambda x: 'on_{}'.format(x),
                                **arguments)

    # If provided, determine the host environment; if it is provided for
    # an object that does not take it, it will fail while trying to update
    # the entitlements. Moreover, if it is not provided for an object that
    # requires it, it will also fail. We thus do not need to perform any
    # kind of verification for that.
    dbenvs = [
        HostEnvironment.get_instance(session, he)
        for he in set(on_host_environment)
    ] if on_host_environment else []

    # Return the values
    return dbtos, dbons, dblocations, dbenvs, dbtype


def get_host_entitlements(dbon, dbtype=None, dbtos=None):
    """Get all entitlements that apply to a host

    This function aims at finding all the entitlements that apply to a given
    host and return an iterable with the results.
    """
    # Prepare the query
    query = object_session(dbon).query(Entitlement)

    # Apply the type conditions if provided
    if dbtype:
        query = query.filter_by(type_id=dbtype.id)

    # Apply conditions on the 'to' field
    if dbtos:
        toconds = []
        grns = [t.eon_id for t in dbtos if isinstance(t, Grn)]
        if grns:
            toconds.append(Entitlement.eon_id.in_(grns))
        users = [t.id for t in dbtos if isinstance(t, User)]
        if users:
            toconds.append(Entitlement.user_id.in_(users))
        if toconds:
            query = query.filter(or_(*toconds))

    # To perform this kind of query, each kind of entitlement needs to be
    # queried against
    onconds = []

    # The host itself
    onconds.append(Entitlement.host_id == dbon.hardware_entity_id)

    # The host's cluster if it has one
    if dbon.cluster:
        onconds.append(Entitlement.cluster_id == dbon.cluster.id)

    # The host's personality, that matches the host's location
    parent_loc_ids = dbon.hardware_entity.location.parent_ids()
    onconds.append(and_(
        Entitlement.personality_id == dbon.personality.id,
        Entitlement.location_id.in_(parent_loc_ids)))

    # The host's archetype, that matches the host's host environment and
    # location
    onconds.append(and_(
        Entitlement.archetype_id == dbon.personality.archetype_id,
        Entitlement.host_environment_id ==
        dbon.personality.host_environment_id,
        Entitlement.location_id.in_(parent_loc_ids)))

    # The host's GRN if it has one, or the host's personality's GRN (if
    # the host does not have one), that matches the host's host
    # environment and location
    onconds.append(and_(
        Entitlement.target_eon_id == dbon.effective_owner_grn.eon_id,
        Entitlement.host_environment_id ==
        dbon.personality.host_environment_id,
        Entitlement.location_id.in_(parent_loc_ids)))

    # Apply conditions on the 'on' field
    query = query.filter(or_(*onconds))

    return query
