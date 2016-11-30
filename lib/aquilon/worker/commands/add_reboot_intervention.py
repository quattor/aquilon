# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013,2014,2015,2016  Contributor
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

from aquilon.aqdb.model import RebootIntervention
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.add_intervention import CommandAddIntervention


class CommandAddRebootIntervention(CommandAddIntervention):

    required_parameters = ["expiry", "reason"]
    resource_class = RebootIntervention

    def add_resource(self, **kwargs):
        return super(CommandAddRebootIntervention, self).add_resource(
            allowusers=None, allowgroups=None, disabled_actions=None, **kwargs)

        # More thorough check reboot_schedule and intervention
        # XXX TODO
        # i) detect week of month of start of intervention
        # ii) detect time
        # iii) compute week of application of reboot_schedule
        # iv) ... and time
        # v) test all the above doesn't conflict within 1hr of each other.

    def render(self, **kwargs):
        return super(CommandAddRebootIntervention, self).render(metacluster=None,
                                                                intervention="reboot_intervention",
                                                                **kwargs)
