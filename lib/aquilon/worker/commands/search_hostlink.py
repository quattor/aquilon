# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008-2015,2018-2019  Contributor
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
"""Contains the logic for `aq search hostlink`."""

from aquilon.aqdb.model import Hostlink
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.search_resource import CommandSearchResource


class CommandSearchHostlink(CommandSearchResource):

    resource_class = Hostlink
    resource_name = "hostlink"

    def filter_by(self, q, target=None, owner=None, group=None,
                  mode=None, **kwargs):
        if target:
            q = q.filter_by(target=target)
        if owner:
            q = q.filter_by(owner_user=owner)
        if group:
            q = q.filter_by(owner_group=group)
        if mode:
            q = q.filter_by(target_mode=mode)

        return q
