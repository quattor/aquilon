# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014-2018  Contributor
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
"""Wrappers for the userinfo table."""

import csv
import subprocess

from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import joinedload, subqueryload

from aquilon.exceptions_ import ArgumentError, PartialError
from aquilon.aqdb.model import (
    Entitlement,
    Personality,
    User,
    UserType,
)
from aquilon.worker.templates import PlenaryPersonality
from aquilon.utils import chunk


class UserSync(object):

    _script_location = ['tool_locations', 'refresh_user_list']

    _convert_fields = {
        'uid': int,
        'gid': int,
    }

    @classmethod
    def _default_compare_fields(cls, x, y):
        return x == y

    @classmethod
    def _default_transform_fields(cls, x):
        return x

    _compare_fields = {
        'type': lambda x, y: x.name == y,
    }

    def __init__(self, config, session, logger, plenaries, incremental=False,
                 ignore_delete_limit=False):
        self._config = config
        self._session = session
        self._logger = logger
        self._plenaries = plenaries
        self._incremental = incremental

        if not config.has_value(*self._script_location):
            raise ArgumentError('User synchronization is disabled.')
        self._script = config.get(*self._script_location)

        if ignore_delete_limit:
            self._limit = None
        else:
            self._limit = config.getint('broker', 'user_delete_limit')

        self._transform_fields = {}
        self._user_type_cache = {}

        try:
            self._default_user_type = get_default_user_type(config)
        except ArgumentError:
            self._default_user_type = None
        self._convert_fields['type'] = self._convert_type
        self._transform_fields['type'] = self._transform_type

    def _convert_type(self, name):
        if not name:
            if self._default_user_type:
                return self._default_user_type
            raise ArgumentError('No default user type, and no type was '
                                'provided; cannot proceed')
        return name

    def _transform_type(self, name):
        if name not in self._user_type_cache:
            self._user_type_cache[name] = \
                UserType.get_unique(self._session, name, compel=True)
        return self._user_type_cache[name]

    def _add_new(self, details):
        dbuser = User(
            name=details['name'], uid=details['uid'], gid=details['gid'],
            full_name=details['full_name'], home_dir=details['home_dir'],
            type=self._transform_fields['type'](details['type']))
        self._session.add(dbuser)

        added = self._commit_if_needed(
            'Adding {user.type.name} user {user.name} '
            '(uid: {user.uid}, gid: {user.gid})'.format(user=dbuser))

        self._added += added
        return dbuser

    def _check_update_existing(self, dbuser, details):
        update_msg = []

        for attr in ('uid', 'gid', 'full_name', 'home_dir', 'type'):
            new = details[attr]
            old = getattr(dbuser, attr)
            same = self._compare_fields.get(attr, self._default_compare_fields)
            if not same(old, new):
                new = self._transform_fields.get(
                    attr, self._default_transform_fields)(new)
                update_msg.append('{} = {}, was {}'.format(
                    attr, getattr(new, 'name', new),
                    getattr(old, 'name', old)))
                setattr(dbuser, attr, new)

        if update_msg:
            updated = self._commit_if_needed(
                'Updating {user.type.name} user {user.name} '
                '({updates})'.format(
                    user=dbuser, updates='; '.join(update_msg)))
            self._updated += updated

    def _report_duplicate_uid(self, new, old):
        msg = 'Duplicate UID: {} is already used by {}, skipping {}.'.format(
            new['uid'], old.name, new['name'])
        if self._incremental:
            self._errors.append(msg)
        else:
            self._logger.client_info(msg)

    def _update_plenaries_on_delete(self, userchunk):
        updated_plenaries = set()
        userset = set(userchunk)

        # Check for root users in the list, and remove their permissions from
        # the personalities
        q = self._session.query(Personality)
        q = q.join(Personality.root_users)
        q = q.filter(User.id.in_(dbuser.id for dbuser in userchunk))
        q = q.options(subqueryload('root_users'),
                      subqueryload('root_netgroups'),
                      joinedload('stages'))
        q = q.options(PlenaryPersonality.query_options(
            prefix='stages.', load_personality=False))
        for personality in q:
            for dbuser in userset & set(personality.root_users):
                personality.root_users.remove(dbuser)

            updated_plenaries.update(personality.stages.values())

        # Check for any entitlement for the given users
        q = self._session.query(Entitlement)
        q = q.filter(Entitlement.user_id.in_(
            dbuser.id for dbuser in userchunk))
        for entit in q:
            if entit.host_id:
                updated_plenaries.add(entit.host)
            elif entit.cluster_id:
                updated_plenaries.add(entit.cluster)
            elif entit.personality_id:
                updated_plenaries.add(entit.personality.stages.values())
            elif entit.archetype_id:
                updated_plenaries.add(entit.archetype)
            elif entit.target_eon_id:
                updated_plenaries.add(entit.target_grn)

        return updated_plenaries

    def _delete_gone(self, userlist):
        if self._limit is not None and len(userlist) > self._limit:
            msg = ('Cowardly refusing to delete {} users, because it is '
                   'over the limit of {}.  Use the --ignore_delete_limit '
                   'option to override.'.format(len(userlist), self._limit))
            if self._incremental:
                self._errors.append(msg)
            else:
                self._logger.client_info(msg)
            return

        updated_plenaries = set()

        # Oracle has limits on the size of the IN clause, so we will need to
        # split the list to smaller chunks
        self._logger.info('Searching all the plenaries that need updating...')
        for userchunk in chunk(userlist, 1000):
            updated_plenaries.update(
                self._update_plenaries_on_delete(userchunk))

        # Add to the plenary collection all the plenaries that have been
        # updated following the deletion of the users
        self._plenaries.add(updated_plenaries)

        for dbuser in userlist:
            self._session.delete(dbuser)
            deleted = self._commit_if_needed(
                'Deleting user {} (uid: {}, gid: {})'.format(
                    dbuser.name, dbuser.uid, dbuser.gid))
            self._deleted += deleted

    def _commit_if_needed(self, msg):
        if self._incremental:
            # Clear the user type cache, as a commit attempt invalidates the
            # database objects
            self._user_type_cache = {}
            try:
                self._session.commit()
                self._logger.debug(msg)
                self._success.append(msg)
                return 1
            except DatabaseError as err:
                # err contains the name of the failed constraint, that's
                # enough to figure out what went wrong
                self._logger.info('Failed: %s (%s)', msg, err)
                self._errors.append('%s (%s)' % (msg, err))
                self._session.rollback()
                return 0
            except Exception as err:
                # General error, better print all the info we have
                self._logger.info('Failed: %s (%s)', msg, err)
                self._errors.append('%s (%s)' % (msg, err))
                self._session.rollback()
                return 0
        else:
            self._logger.debug(msg)
            return 1

    def get_current_users(self, *by):
        dbusers = self._session.query(User)

        users = {attr: {} for attr in by} if by else []
        self._logger.info('Listing current users...')
        for dbuser in dbusers:
            if by:
                for attr in by:
                    users[attr][getattr(dbuser, attr)] = dbuser
            else:
                users.append(dbuser)
        self._logger.info('Found {} users'.format(
            len(users[by[0]] if by else users)))

        return users

    def _run_script(self):
        cmd = [self._script, '--format', 'csv', '--csv-delimiter', ',']
        self._logger.info('Running: {}'.format(subprocess.list2cmdline(cmd)))
        run_script = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1
        )

        # Yield each line found on the standard output
        for line in iter(run_script.stdout.readline, b''):
            yield line.strip()

        # At the end of the run, show each line found on the standard error
        stderr = run_script.communicate()[1]
        for line in stderr.splitlines():
            self._logger.info(line)

        # Get the return code; if there was any issue, raise an exception
        self._logger.info('Reached the end of the script execution')
        retcode = run_script.poll()
        if retcode:
            raise subprocess.CalledProcessError(retcode, cmd, output=stderr)

    def read_users(self):
        reader = csv.DictReader(self._run_script(), delimiter=',')
        for row in reader:
            # Try to convert the fields that need conversion
            try:
                for k, v in self._convert_fields.items():
                    row[k] = v(row.get(k))
            except Exception as e:
                self._logger.info('{}, skipping: {}.'.format(str(e), row))
                continue

            yield row

    def refresh_user(self):
        self._success = []
        self._errors = []
        self._added = 0
        self._deleted = 0
        self._updated = 0

        # Get the list of users by uid and by name, this will be the base list
        # to know which users we have in extra at the end, and identify any
        # duplicate UID we might have
        users = self.get_current_users('uid', 'name')

        for user in self.read_users():
            # Go through the users that the script returns
            if user['name'] not in users['name']:
                # If the user name is not in the list of users we already
                # have in the database
                if user['uid'] in users['uid']:
                    # But the UID already exists in the database (as another
                    # user, it means), then we need to show an error
                    self._report_duplicate_uid(
                        user, users['uid'][user['uid']])
                    continue

                # If we reach here, just create the new user with the
                # information we just read
                dbuser = self._add_new(user)
                if dbuser:
                    # And add the newly-created user to the list we store of
                    # users by UID, that way we will be able to catch any
                    # future UID conflict. Note that we do not add the user to
                    # the list we store by name, as that latter will be used
                    # at the end to remove all users that were not in the list
                    # we parsed from the script
                    users['uid'][dbuser.uid] = dbuser
            else:
                # If the user name is in the list, then get the database user
                # that corresponds to it
                dbuser = users['name'][user['name']]

                if user['uid'] != dbuser.uid:
                    # If the UID that we got from the database is different
                    # from the one returned by the script
                    if user['uid'] in users['uid']:
                        # And if the UID returned by the script is an UID that
                        # already exists in the list by UID, then we need to
                        # show an error. We do not remove the user from the
                        # list by name, so that it will be removed from the
                        # database at the end of that process.
                        self._report_duplicate_uid(
                            user, users['uid'][user['uid']])
                        continue

                    # If we reach here, we can just replace the mention of the
                    # user by UID: we remove the old UID reference to that
                    # user, and we add a reference for the new UID
                    del users['uid'][dbuser.uid]
                    users['uid'][user['uid']] = dbuser

                del users['name'][dbuser.name]

                self._check_update_existing(dbuser, user)

        # Delete all the users left in the list of users by name, considering
        # that each user we have seen in the received list has been removed
        # from here, meaning all that is left is to be removed from the
        # database
        self._delete_gone(users['name'].values())

        self._session.flush()

        self._plenaries.write()

        if self._errors:
            raise PartialError(success=self._success, failed=self._errors)
        else:
            self._logger.client_info(
                'Added {}, deleted {}, updated {} users.'.format(
                    self._added, self._deleted, self._updated))


def get_default_user_type(config):
    user_type = None

    default_user_type_section = ['broker', 'default_user_type']
    if config.has_value(*default_user_type_section):
        user_type = config.get(*default_user_type_section)

    if not user_type:
        raise ArgumentError("Cannot determine the type of the user.  "
                            "Please specify --type.")

    return user_type
