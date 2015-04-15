# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014  Contributor
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

from aquilon.aqdb.model import Application
from aquilon.utils import validate_nlist_key
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.grn import lookup_grn
from aquilon.worker.dbwrappers.resources import (add_resource,
                                                 get_resource_holder)


class CommandAddApplication(BrokerCommand):

    required_parameters = ["application"]

    def render(self, session, logger, application, eonid, eon_id, grn, hostname,
               cluster, metacluster, resourcegroup, comments, **arguments):
        validate_nlist_key("application", application)
        holder = get_resource_holder(session, logger, hostname, cluster,
                                     metacluster, resourcegroup, compel=False)

        Application.get_unique(session, name=application, holder=holder,
                               preclude=True)

        # Backwards compatibility
        if eonid is not None:
            self.deprecated_option("eonid", "Please use --eon_id or --grn "
                                   "instead.", logger=logger, **arguments)
            eon_id = eonid

        dbgrn = lookup_grn(session, grn, eon_id, logger=logger,
                           config=self.config)

        dbapp = Application(name=application, comments=comments, grn=dbgrn)
        return add_resource(session, logger, holder, dbapp)
