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

from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import contains_eager
from sqlalchemy.util import KeyedTuple

from aquilon.exceptions_ import ArgumentError, PartialError
from aquilon.aqdb.model import User, Personality
from aquilon.worker.templates import Plenary, PlenaryCollection

LOGGER = logging.getLogger(__name__)


class UserSync(object):
    # Labels for the passwd entries - the order must match the file format
    labels = ("name", "passwd", "uid", "gid", "full_name", "home_dir", "shell")

    def __init__(self, config, session, logger=LOGGER, incremental=False,
                 ignore_delete_limit=False):
        self.session = session
        self.logger = logger
        self.plenaries = PlenaryCollection(logger=logger)
        self.incremental = incremental
        self.success = []
        self.errors = []
        self.added = 0
        self.deleted = 0
        self.updated = 0

        if not config.get("broker", "user_list_location"):
            raise ArgumentError("User synchronization is disabled.")

        self.fname = config.get("broker", "user_list_location")

        if ignore_delete_limit:
            self.limit = None
        else:
            self.limit = config.getint("broker", "user_delete_limit")

    def commit_if_needed(self, msg):
        if self.incremental:
            try:
                self.session.commit()
                self.logger.debug(msg)
                self.success.append(msg)
                return 1
            except DatabaseError as err:
                # err.message contains the name of the failed constraint, that's
                # enough to figure out what went wrong
                self.logger.info("Failed: %s (%s)" % (msg, err.message.strip()))
                self.errors.append("%s (%s)" % (msg, err.message.strip()))
                self.session.rollback()
                return 0
            except Exception as err:
                # General error, better print all the info we have
                self.logger.info("Failed: %s (%s)" % (msg, err))
                self.errors.append("%s (%s)" % (msg, err))
                self.session.rollback()
                return 0
        else:
            self.logger.debug(msg)
            return 1

    def add_new(self, details):
        dbuser = User(name=details.name, uid=details.uid, gid=details.gid,
                      full_name=details.full_name, home_dir=details.home_dir)
        self.session.add(dbuser)

        added = self.commit_if_needed("Adding user %s (uid: %s, gid: %s)" %
                                      (details.name, details.uid, details.gid))
        self.added += added
        return dbuser

    def check_update_existing(self, dbuser, details):
        update_msg = []
        for attr, type_ in (("uid", int),
                            ("gid", int),
                            ("full_name", str),
                            ("home_dir", str)):
            # Type conversion is important, otherwise numeric uid in the DB
            # would not match string uid from input
            old = getattr(dbuser, attr)
            new = type_(getattr(details, attr))
            if old != new:
                update_msg.append("%s = %s, was %s" % (attr, new, old))
                setattr(dbuser, attr, new)

        if update_msg:
            updated = self.commit_if_needed("Updating user %s (%s)" %
                                            (dbuser.name, "; ".join(update_msg)))
            self.updated += updated

    def delete_gone(self, userlist):
        if self.limit is not None and len(userlist) > self.limit:
            msg = "Cowardly refusing to delete %s users, because it's " \
                "over the limit of %s.  Use the --ignore_delete_limit " \
                "option to override." % (len(userlist), self.limit)
            if self.incremental:
                self.errors.append(msg)
            else:
                self.logger.client_info(msg)
            return

        personalities = set()

        def chunk(list_, size):
            for i in xrange(0, len(list_), size):
                yield list_[i:i + size]

        # Oracle has limits on the size of the IN clause, so we'll need to split the
        # list to smaller chunks
        for userchunk in chunk(userlist, 1000):
            userset = set(userchunk)
            q = self.session.query(Personality)
            q = q.join(Personality.root_users)
            q = q.options(contains_eager('root_users'))
            q = q.filter(User.id.in_([dbuser.id for dbuser in userchunk]))
            for p in q:
                for dbuser in userset & set(p.root_users):
                    p.root_users.remove(dbuser)
                personalities.add(p)

        self.plenaries.extend([Plenary.get_plenary(p) for p in personalities])

        for dbuser in userlist:
            self.session.delete(dbuser)
            deleted = self.commit_if_needed("Deleting user %s (uid: %s, gid: %s)" %
                                            (dbuser.name, dbuser.uid,
                                             dbuser.gid))
            self.deleted += deleted

    def report_duplicate_uid(self, new, old):
        msg = "Duplicate UID: %s is already used by %s, skipping %s." % \
            (new.uid, old.name, new.name)
        if self.incremental:
            self.errors.append(msg)
        else:
            self.logger.client_info(msg)

    def refresh_user(self):
        q = self.session.query(User)
        by_name = {}
        by_uid = {}
        for dbuser in q.all():
            by_name[dbuser.name] = dbuser
            by_uid[dbuser.uid] = dbuser

        for line in open(self.fname):
            try:
                user_name, rest = line.split('\t')
            except ValueError:
                self.logger.info("Failed to unpack, skipping line: %s", line)
                continue

            if user_name.startswith("YP_"):
                continue

            fields = rest.split(':')
            if len(fields) != len(self.labels):
                self.logger.info("Unexpected number of fields, "
                                 "skipping line: %s", line)
                continue

            try:
                fields[2] = int(fields[2])
            except ValueError:
                self.logger.info("UID is not a number, skipping line: %s", line)
                continue

            try:
                fields[3] = int(fields[3])
            except ValueError:
                self.logger.info("GID is not a number, skipping line: %s", line)
                continue

            details = KeyedTuple(fields, labels=self.labels)

            if details.name not in by_name:
                if details.uid in by_uid:
                    self.report_duplicate_uid(details, by_uid[details.uid])
                    continue

                dbuser = self.add_new(details)
                if dbuser:
                    by_uid[dbuser.uid] = dbuser
            else:
                dbuser = by_name[details.name]

                if details.uid != dbuser.uid:
                    if details.uid in by_uid:
                        self.report_duplicate_uid(details, by_uid[details.uid])
                        continue

                    del by_uid[dbuser.uid]
                    by_uid[details.uid] = dbuser

                del by_name[dbuser.name]

                self.check_update_existing(dbuser, details)

        self.delete_gone(by_name.values())

        self.session.flush()

        self.plenaries.write()

        if self.errors:
            raise PartialError(success=self.success, failed=self.errors)
        else:
            self.logger.client_info("Added %d, deleted %d, updated %d users." %
                                    (self.added, self.deleted, self.updated))

        return
