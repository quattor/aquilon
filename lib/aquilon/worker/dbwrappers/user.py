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

from sqlalchemy.orm import contains_eager
from sqlalchemy.util import KeyedTuple

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import User, Personality
from aquilon.worker.templates import Plenary, PlenaryCollection

LOGGER = logging.getLogger(__name__)


def refresh_user(config, session, logger=LOGGER):
    if not config.get("broker", "user_list_location"):
        raise ArgumentError("User synchronization is disabled.")

    q = session.query(User)
    users = {}
    for dbuser in q.all():
        users[dbuser.name] = dbuser

    fname = config.get("broker", "user_list_location")

    # Labels for the passwd entries - the order must match the file format
    labels = ("name", "passwd", "uid", "gid", "full_name", "home_dir", "shell")

    added = 0
    deleted = 0
    updated = 0
    for line in open(fname):
        user_name, rest = line.split('\t')
        if user_name.startswith("YP_"):
            continue
        details = KeyedTuple(rest.split(':'), labels=labels)

        if  details.name not in users:
            logger.debug("Adding user %s (uid: %s, gid: %s)" %
                         (details.name, details.uid, details.gid))
            dbuser = User(name=details.name, uid=details.uid,
                          gid=details.gid, full_name=details.full_name,
                          home_dir=details.home_dir)
            session.add(dbuser)
            added += 1
            continue

        # Already exists
        dbuser = users[details.name]
        del users[details.name]

        changed = False
        for attr, type_ in (("uid", int),
                            ("gid", int),
                            ("full_name", str),
                            ("home_dir", str)):
            # Type conversion is important, otherwise numeric uid in the DB
            # would not match string uid from input
            old = getattr(dbuser, attr)
            new = type_(getattr(details, attr))
            if old != new:
                logger.debug("Updating user %s (set %s to %s, was %s)" %
                             (dbuser.name, attr, new, old))
                setattr(dbuser, attr, new)
                changed = True

        if changed:
            updated += 1

    plenaries = PlenaryCollection(logger=logger)
    personalities = set()

    def chunk(list_, size):
        for i in xrange(0, len(list_), size):
            yield list_[i:i+size]

    # Oracle has limits on the size of the IN clause, so we'll need to split the
    # list to smaller chunks
    for userchunk in chunk(users.values(), 1000):
        userset = set(userchunk)
        q = session.query(Personality)
        q = q.join(Personality.root_users)
        q = q.options(contains_eager('root_users'))
        q = q.filter(User.id.in_([dbuser.id for dbuser in userchunk]))
        for p in q:
            for dbuser in userset & set(p.root_users):
                p.root_users.remove(dbuser)
            personalities.add(p)

    plenaries.extend([Plenary.get_plenary(p) for p in personalities])

    for dbuser in users.values():
        logger.debug("Deleting user %s (uid: %s, gid: %s)" %
                     (dbuser.name, dbuser.uid, dbuser.gid))
        session.delete(dbuser)
        deleted += 1

    session.flush()

    plenaries.write()
    logger.client_info("Added %d, deleted %d, updated %d users." %
                       (added, deleted, updated))

    return
