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
"""Contains the logic for `aq show active locks`."""


from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.locks import lock_queue


class CommandShowActiveLocks(BrokerCommand):

    requires_transaction = False
    requires_azcheck = False
    defer_to_thread = False
    # Even though this class imports lock_queue, it doesn't take any locks!
    _is_lock_free = True

    def render(self, **arguments):
        retval = []
        for key in lock_queue.queue[:]:
            description = "Defunct lock: "
            if hasattr(key.logger, "get_status"):
                status = key.logger.get_status()
                if status and status.description:
                    description = status.description + ' '
            retval.append("%s%s %s" % (description, key.state, key))
        return str("\n".join(retval))
