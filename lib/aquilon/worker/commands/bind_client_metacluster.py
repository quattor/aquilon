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
"""Contains the logic for `aq bind client --metacluster`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import MetaCluster, Service
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.services import Chooser
from aquilon.worker.dbwrappers.service_instance import get_service_instance
from aquilon.worker.templates import PlenaryCollection


class CommandBindClientMetacluster(BrokerCommand):

    required_parameters = ["metacluster", "service"]

    def render(self, session, logger, metacluster, service, instance,
               force=False, **arguments):
        dbmeta = MetaCluster.get_unique(session, metacluster, compel=True)
        dbservice = Service.get_unique(session, service, compel=True)
        if instance:
            dbinstance = get_service_instance(session, dbservice, instance)
        else:
            dbinstance = None

        choosers = []
        failed = []
        # FIXME: this logic should be in the chooser
        for dbobj in dbmeta.all_objects():
            # Always add the binding on the cluster we were called on
            if dbobj == dbmeta or dbservice in dbobj.required_services:
                chooser = Chooser(dbobj, logger=logger, required_only=False)
                choosers.append(chooser)
                try:
                    chooser.set_single(dbservice, dbinstance, force=force)
                except ArgumentError as err:
                    failed.append(str(err))

        if failed:
            raise ArgumentError("The following objects failed service "
                                "binding:\n%s" % "\n".join(failed))

        session.flush()

        plenaries = PlenaryCollection(logger=logger)
        plenaries.extend(chooser.plenaries for chooser in choosers)
        plenaries.flatten()

        plenaries.write()

        return
