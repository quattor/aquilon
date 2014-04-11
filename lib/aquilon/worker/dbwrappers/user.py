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
"""Wrappers for the user_principal table."""


import logging

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import User, Personality
from aquilon.worker.templates import PlenaryCollection
from sqlalchemy.orm import subqueryload, joinedload


LOGGER = logging.getLogger(__name__)

def refresh_user(config, session, logger):
    if not config.get("broker", "user_list_location"):
        raise ArgumentError("User synchronization is disabled.")

    q = session.query(User)
    users = {}
    for dbuser in q.all():
        users[dbuser.name] = dbuser

    fname = config.get("broker", "user_list_location")

    added = 0
    deleted = 0
    updated = 0
    for line in open(fname):
        user_name, rest = line.split('\t')
        if user_name.startswith("YP_"):
            continue
        details = rest.split(':')

        if  user_name not in users:
            dbuser = User(name=user_name, uid=details[2],
                          gid=details[3], full_name=details[4],
                          home_dir=details[5])
            session.add(dbuser)
            added += 1
        else:
            # already exists
            dbuser = users[user_name]
            del users[user_name]
            if dbuser.uid != details[2] or \
               dbuser.gid != details[3] or \
               dbuser.name != details[4] or \
               dbuser.home_dir != details[5] :
                dbuser.uid = details[2]
                dbuser.gid = details[3]
                dbuser.name = details[4]
                dbuser.home_dir = details[5]
                updated += 1

    plenaries = PlenaryCollection(logger=logger)
    plist = ()

    q = session.query(Personality)
    q = q.options(joinedload('root_users'), subqueryload('root_users'))
    personalities = q.all()

    for p in personalities:
        for dbuser in users.values():
            if dbuser in p.root_users:
                p.root_users.remove(dbuser)
                plist.append(p)
        session.delete(dbuser)
    deleted = len(users.values())

    plenaries.extend([Plenary.get_plenary(p) for p in plist])
    plenaries.write()
    if logger:
        logger.client_info("Added %d, deleted %d, update %d Users." %
                           (added, deleted, updated))
    session.flush()
    return
