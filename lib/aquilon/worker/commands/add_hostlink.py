# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014,2015,2016  Contributor
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
"""Contains the logic for `aq add hostlink`."""

from aquilon.aqdb.model import Hostlink
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.add_resource import CommandAddResource


class CommandAddHostlink(CommandAddResource):

    required_parameters = ["hostlink", "target", "owner"]
    resource_class = Hostlink
    resource_name = "hostlink"

    def add_resource(self, session, logger, hostlink, target, owner, group,
                     comments, **_):
        dbhl = Hostlink(name=hostlink, target=target, owner_user=owner,
                        owner_group=group, comments=comments)
        return dbhl
