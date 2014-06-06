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

from sqlalchemy.sql import func

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import User
from aquilon.worker.broker import BrokerCommand


class CommandAddUser(BrokerCommand):

    required_parameters = ["username"]

    def render(self, session, username, uid, autouid, gid, full_name,
               home_directory, **arguments):
        User.get_unique(session, username, preclude=True)

        if autouid:
            # Prevent concurrent invocations
            q = session.query(User.id).order_by(User.id)
            session.execute(q.with_lockmode('update'))

            last_uid = session.query(func.max(User.uid)).scalar()
            uid = last_uid + 1
        else:
            q = session.query(User)
            q = q.filter_by(uid=uid)
            if q.first():
                raise ArgumentError("UID %s is already in use." % uid)

        dbuser = User(name=username, uid=uid, gid=gid, full_name=full_name,
                      home_dir=home_directory)
        session.add(dbuser)

        session.flush()

        return
