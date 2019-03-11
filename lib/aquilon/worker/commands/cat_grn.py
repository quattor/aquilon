# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008-2018  Contributor
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
"""Contains the logic for `aq cat --grn`."""

from aquilon.aqdb.model import (
    HostEnvironment,
    ParameterizedGrn,
    ResourceGroup,
)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.grn import lookup_grn
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.dbwrappers.resources import get_resource
from aquilon.worker.templates import (
    Plenary,
    PlenaryResource,
)


class CommandCatGrn(BrokerCommand):

    required_parameters = ["grn"]

    # We do not lock the plenary while reading it
    _is_lock_free = True

    def render(self, generate, session, logger, grn, eon_id, host_environment,
               **arguments):
        dbgrn = lookup_grn(session, grn, eon_id, logger=logger,
                           config=self.config)
        dbenv = HostEnvironment.get_unique(
            session, host_environment, compel=True)
        dbloc = get_location(session, compel=True, **arguments)
        holder = ParameterizedGrn(dbgrn, dbenv, dbloc)

        dbresource = get_resource(session, holder, **arguments)
        if dbresource:
            if isinstance(dbresource, ResourceGroup):
                cls = PlenaryResource
            else:
                cls = Plenary
            plenary_info = cls.get_plenary(dbresource, logger=logger)
        else:
            plenary_info = Plenary.get_plenary(holder, logger=logger)

        if generate:
            return plenary_info._generate_content()
        else:
            return plenary_info.read()
