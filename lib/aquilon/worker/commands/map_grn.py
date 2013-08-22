# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
from aquilon.aqdb.model import Personality
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.grn import lookup_grn
from aquilon.worker.dbwrappers.host import (hostname_to_host, hostlist_to_hosts,
                                            check_hostlist_size)
from aquilon.worker.templates.personality import PlenaryPersonality


class CommandMapGrn(BrokerCommand):

    required_parameters = ["target"]

    def _update_dbobj(self, obj, target, grn):

        # Don't add twice the same tuple
        for grn_rec in obj._grns:
            if (obj == grn_rec.mapped_object and
                grn == grn_rec.grn and
                target == grn_rec.target):
                return

        obj.grns.append((obj, grn, target))

    def render(self, session, logger, target, grn, eon_id, hostname, list, personality,
               archetype, **arguments):
        dbgrn = lookup_grn(session, grn, eon_id, logger=logger,
                           config=self.config)

        target_type = "personality" if personality else "host"

        if hostname:
            objs = [hostname_to_host(session, hostname)]
        elif list:
            check_hostlist_size(self.command, self.config, list)
            objs = hostlist_to_hosts(session, list)
        elif personality:
            objs = [Personality.get_unique(session, name=personality,
                                           archetype=archetype, compel=True)]

        for obj in objs:
            # INFO: Fails for archetypes other than 'aquilon', 'vmhost'
            valid_targets = self.config.get("archetype_" + obj.archetype.name,
                                            target_type + "_grn_targets")

            if target not in map(lambda s: s.strip(), valid_targets.split(",")):
                raise ArgumentError("Invalid %s target %s for archetype %s, please "
                                    "choose from %s" % (target_type, target,
                                                        obj.archetype.name,
                                                        valid_targets))

            self._update_dbobj(obj, target, dbgrn)

        session.flush()

        if personality:
            plenary = PlenaryPersonality(objs[0], logger=logger)
            plenary.write()

        return
