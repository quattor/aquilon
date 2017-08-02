# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2013,2014,2015,2016  Contributor
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
"""Contains the logic for `aq add intervention`."""

from datetime import datetime

from dateutil.parser import parse

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Intervention
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.add_resource import CommandAddResource


class CommandAddIntervention(CommandAddResource):

    required_parameters = ["expiry", "intervention", "reason"]
    resource_class = Intervention
    resource_name = "intervention"

    def setup_resource(self, session, logger, dbiv, reason, expiry, start_time,
                       allowusers, allowgroups, disabled_actions, **_):
        try:
            expire_when = parse(expiry)
        except (ValueError, TypeError) as err:
            raise ArgumentError("The expiry value '%s' could not be "
                                "interpreted: %s" % (expiry, err))

        now = datetime.utcnow().replace(microsecond=0)
        if start_time is None:
            start_when = now
        else:
            try:
                start_when = parse(start_time)
            except (ValueError, TypeError) as e:
                raise ArgumentError("The start time '%s' could not be "
                                    "interpreted: %s" % (start_time, e))

        if start_when > expire_when:
            raise ArgumentError("The start time is later than the expiry time.")

        if start_when < now or expire_when < now:
            raise ArgumentError("The start time or expiry time are in the past.")

        dbiv.expiry_date = expire_when
        dbiv.start_date = start_when
        dbiv.users = allowusers
        dbiv.groups = allowgroups
        dbiv.disabled = disabled_actions
        dbiv.reason = reason
