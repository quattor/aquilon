# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013,2014  Contributor
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

from dateutil.parser import parse
from datetime import datetime

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import RebootIntervention
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.resources import (add_resource,
                                                 get_resource_holder)


class CommandAddRebootIntervention(BrokerCommand):

    required_parameters = ["expiry", "justification"]

    def render(self, session, logger, expiry, start_time,
               comments, justification, hostname, cluster,
               **arguments):

        allowusers = None
        allowgroups = None
        disabled_actions = None

        # Name for the plenary and show_host output
        intervention = 'reboot_intervention'

        try:
            expire_when = parse(expiry)
        except ValueError as e:
            raise ArgumentError("the expiry value '%s' could not be "
                                "interpreted: %s" % (expiry, e))

        now = datetime.utcnow().replace(microsecond=0)
        if start_time is None:
            start_when = now
        else:
            try:
                start_when = parse(start_time)

            except ValueError as e:
                raise ArgumentError("the start time '%s' could not be "
                                    "interpreted: %s" % (start_time, e))

        if start_when > expire_when:
            raise ArgumentError("the start time is later than the expiry time")

        if (start_when < now) or (expire_when < now):
            raise ArgumentError("The start time or expiry time are in the past.")

        # More thorough check reboot_schedule and intervention
        # XXX TODO
        # i) detect week of month of start of intervention
        # ii) detect time
        # iii) compute week of application of reboot_schedule
        # iv) ... and time
        # v) test all the above doesn't conflict within 1hr of each other.

        # Setup intervention
        holder = get_resource_holder(session, hostname, cluster, compel=False)

        RebootIntervention.get_unique(session, name=intervention,
                                      holder=holder, preclude=True)

        dbiv = RebootIntervention(name=intervention,
                                  expiry_date=expire_when,
                                  start_date=start_when,
                                  users=allowusers,
                                  groups=allowgroups,
                                  disabled=disabled_actions,
                                  comments=comments,
                                  justification=justification)

        return add_resource(session, logger, holder, dbiv)
