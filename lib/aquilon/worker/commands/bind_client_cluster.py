# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014,2015,2016,2017  Contributor
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
"""Contains the logic for `aq bind client --cluster`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Cluster, Service, ServiceInstance
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.services import Chooser, ChooserCache
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandBindClientCluster(BrokerCommand):
    requires_plenaries = True

    required_parameters = ["cluster", "service"]

    def render(self, session, logger, plenaries, cluster, service, instance, user,
               justification, reason, force=False,**_):

        dbcluster = Cluster.get_unique(session, cluster, compel=True)

        # Validate ChangeManagement
        cm = ChangeManagement(session, user, justification, reason, logger, self.command)
        cm.consider(dbcluster)
        cm.validate()

        dbservice = Service.get_unique(session, service, compel=True)
        if instance:
            dbinstance = ServiceInstance.get_unique(session, service=dbservice,
                                                    name=instance, compel=True)
        else:
            dbinstance = None

        chooser_cache = ChooserCache()
        failed = []
        # FIXME: this logic should be in the chooser
        for dbobj in dbcluster.all_objects():
            # Always add the binding on the cluster we were called on
            if dbobj == dbcluster or dbservice in dbobj.required_services:
                chooser = Chooser(dbobj, plenaries, logger=logger,
                                  required_only=False, cache=chooser_cache)
                try:
                    chooser.set_single(dbservice, dbinstance, force=force)
                except ArgumentError as err:
                    failed.append(str(err))

        if failed:
            raise ArgumentError("The following objects failed service "
                                "binding:\n%s" % "\n".join(failed))

        session.flush()

        plenaries.flatten()
        plenaries.write()

        return
