# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014  Contributor
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
"""Contains the logic for `aq manage --metacluster`."""

from aquilon.aqdb.model import MetaCluster
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.manage_list import CommandManageList


class CommandManageMetaCluster(CommandManageList):

    required_parameters = ["metacluster"]

    def get_objects(self, session, metacluster, **arguments):  # pylint: disable=W0613
        dbmeta = MetaCluster.get_unique(session, metacluster, compel=True)
        return (dbmeta.branch, dbmeta.sandbox_author,
                list(dbmeta.all_objects()))
