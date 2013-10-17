# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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
"""Contains the logic for `aq show sandbox --sandbox`."""

from sqlalchemy.orm import joinedload, undefer

from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.exceptions_ import ArgumentError
from aquilon.worker.dbwrappers.sandbox import get_sandbox
from aquilon.worker.formats.branch import AuthoredSandbox


class CommandShowSandboxSandbox(BrokerCommand):

    required_parameters = ["sandbox"]

    def render(self, session, logger, sandbox, pathonly, **arguments):
        (mysandbox, dbauthor) = get_sandbox(session, logger, sandbox,
                                            query_options=[undefer('comments'),
                                                           joinedload('owner')])
        if dbauthor:
            mysandbox = AuthoredSandbox(mysandbox, dbauthor)
        if not pathonly:
            return mysandbox
        if not dbauthor:
            raise ArgumentError("Must specify sandbox as author/branch "
                                "when using --pathonly")
        return mysandbox.path
