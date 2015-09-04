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
"""Contains the logic for `aq cat --metacluster`."""

from aquilon.aqdb.model import MetaCluster
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.resources import get_resource
from aquilon.worker.templates import (Plenary,
                                      PlenaryMetaClusterObject,
                                      PlenaryMetaClusterData)


class CommandCatMetaCluster(BrokerCommand):

    required_parameters = ["metacluster"]

    # We do not lock the plenary while reading it
    _is_lock_free = True

    def render(self, session, logger, metacluster, data, generate, **arguments):
        dbmeta = MetaCluster.get_unique(session, metacluster, compel=True)
        dbresource = get_resource(session, dbmeta, **arguments)
        if dbresource:
            plenary_info = Plenary.get_plenary(dbresource, logger=logger)
        else:
            if data:
                cls = PlenaryMetaClusterData
            else:
                cls = PlenaryMetaClusterObject

            plenary_info = cls.get_plenary(dbmeta, logger=logger)

        if generate:
            return plenary_info._generate_content()
        else:
            return plenary_info.read()
