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
"""Contains the logic for `aq add_entitlement`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import (
    Archetype,
    Grn,
    Organization,
    Parameterized,
    Personality,
)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.change_management import ChangeManagement
from aquilon.worker.dbwrappers.entitlement import (
    get_entitlement_class_for,
    get_entitlements_options,
)

from itertools import product


class CommandAddEntitlement(BrokerCommand):

    requires_plenaries = True
    required_parameters = []

    def _update_entitlements(self, dbon, mapcls, parameters):
        # Determine if the entitlement is for an user or a grn
        entitlements = (dbon.entitled_users if 'user' in parameters
                        else dbon.entitled_grns)

        # Determine if the entitlement type authorizes to entitle the kind
        # of object we received to entitle; this is done here as it only
        # applies to _add_ new entitlements
        if 'user' in parameters:
            is_enabled = any(m.user_type_id == parameters['user'].type_id
                             for m in parameters['type'].to_user_types)
            check_type = '{} User'.format(parameters['user'].type.name.title())
        else:
            is_enabled = parameters['type'].to_grn
            check_type = 'Grn'

        if not is_enabled:
            raise ArgumentError('Entitlement type \'{}\' does not allow '
                                'entitlements to {}'.format(
                                    parameters['type'].name,
                                    check_type))

        # We do not want to add twice the same entitlement, we thus need
        # to go through all the entitlements for the dbon, and check if
        # we find an entitlement for which all the parameters match the
        # one we are trying to add. If it is the case, we do not need to
        # add it again.
        for entitlement in entitlements:
            if all(v == getattr(entitlement, k)
                    for k, v in parameters.items()):
                return False

        # If we reach here, add the entitlement
        entitlements.append(mapcls(**parameters))

        # Return True if that lead to a change
        return True

    def render(self, session, logger, plenaries, user, justification, reason,
               **arguments):
        # Parse the options to get the entitlements options
        dbtos, dbons, dblocations, dbenvs, dbtype = get_entitlements_options(
            session=session, logger=logger, config=self.config,
            on_single_type=True, requires_type=True, **arguments)

        # If we were not able to determine who to entitle, raise an exception
        if not dbtos:
            raise ArgumentError('No GRN nor User provided')

        # If we were not able to determine what we entitle, raise an exception
        if not dbons:
            raise ArgumentError('No target provided')

        # If a location is not provided for an object that requires it, use
        # the default organization of the broker.
        if not dblocations and (
                isinstance(dbons[0], Personality) or
                isinstance(dbons[0], Archetype) or
                isinstance(dbons[0], Grn)):
            dblocations = [Organization.get_unique(
                session, self.config.get('broker', 'default_organization'),
                compel=True), ]

        # Validate ChangeManagement, we will check the host environment if it
        # is directly provided, or fallback on checking the object so the
        # ChangeManagement class will do the job of finding the affected
        # host environments
        cm = ChangeManagement(session, user, justification, reason, logger,
                              self.command, **arguments)
        for dbconsider in (dbenvs or dbons):
            cm.consider(dbconsider)
        cm.validate()

        def dictproduct(**kwargs):
            keys = []
            values = []
            for k, v in kwargs.items():
                if v:
                    keys.append(k)
                    values.append(v)
            for dataset in product(*values):
                yield dict(zip(keys, dataset))

        # Run the method to update the entitlements for the given dbons, with
        # each set of parameters necessary for the received to, locations and
        # host environments
        for parameters in dictproduct(on=dbons, to=dbtos, location=dblocations,
                                      host_environment=dbenvs):
            dbon = parameters.pop('on')
            dbto = parameters.pop('to')
            parameters[dbto.__class__.__name__.lower()] = dbto
            parameters['type'] = dbtype
            mapcls = get_entitlement_class_for(dbon, dbto)
            updated = self._update_entitlements(dbon, mapcls, parameters)

            if updated:
                params = [v for k, v in parameters.items()
                          if k in ['location', 'host_environment']]
                plenobj = (Parameterized.get(dbon, *params)
                           if params else dbon)
                plenaries.add(plenobj)

        # Flush the session
        session.flush()

        # Write the plenaries
        plenaries.write()
