# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
"""Contains the logic for `aq map grn`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Personality, Cluster
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.host import (hostname_to_host, hostlist_to_hosts,
                                            check_hostlist_size)
from aquilon.worker.templates.base import Plenary, PlenaryCollection


class CommandUnMapGrnClearAll(BrokerCommand):

    required_parameters = ["target"]

    def render(self, session, logger, target, hostname, list, membersof,
               personality, archetype, **arguments):

        target_type = "personality" if personality else "host"

        if hostname:
            objs = [hostname_to_host(session, hostname)]
        elif list:
            check_hostlist_size(self.command, self.config, list)
            objs = hostlist_to_hosts(session, list)
        elif membersof:
            dbcluster = Cluster.get_unique(session, membersof, compel=True)
            objs = dbcluster.hosts
        elif personality:
            objs = [Personality.get_unique(session, name=personality,
                                           archetype=archetype, compel=True)]

        plenaries = PlenaryCollection(logger=logger)
        for obj in objs:
            # INFO: Fails for archetypes other than 'aquilon', 'vmhost'
            valid_targets = self.config.get("archetype_" + obj.archetype.name,
                                            target_type + "_grn_targets")

            if target not in [s.strip() for s in valid_targets.split(",")]:
                raise ArgumentError("Invalid %s target %s for archetype %s, please "
                                    "choose from %s" % (target_type, target,
                                                        obj.archetype.name,
                                                        valid_targets))

            for grn_rec in obj._grns[:]:
                if target == grn_rec.target:
                    obj._grns.remove(grn_rec)
            plenaries.append(Plenary.get_plenary(obj))

        session.flush()

        plenaries.write()

        return
