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
"""Contains the logic for `aq update sandbox`."""


from aquilon.exceptions_ import AuthorizationException
from aquilon.aqdb.model import Sandbox
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.branch import expand_compiler


class CommandUpdateSandbox(BrokerCommand):

    required_parameters = ["sandbox"]

    def render(self, session, dbuser, sandbox, comments, compiler_version,
               autosync, **arguments):
        dbsandbox = Sandbox.get_unique(session, sandbox, compel=True)

        # FIXME: proper authorization
        if dbsandbox.owner != dbuser and dbuser.role.name != 'aqd_admin':
            raise AuthorizationException("Only the owner or an AQD admin can "
                                         "update a sandbox.")

        if comments:
            dbsandbox.comments = comments
        if compiler_version:
            dbsandbox.compiler = expand_compiler(self.config, compiler_version)
        if autosync is not None:
            dbsandbox.autosync = autosync

        session.flush()
        return
