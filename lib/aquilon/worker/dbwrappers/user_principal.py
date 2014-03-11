# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013,2014  Contributor
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


import re
import logging

from sqlalchemy.orm import contains_eager, joinedload

from aquilon.exceptions_ import ArgumentError, InternalError, NotFoundException
from aquilon.aqdb.model import Role, Realm, UserPrincipal


LOGGER = logging.getLogger(__name__)
principal_re = re.compile(r'^(.+)@([^@]+)$')
host_re = re.compile(r'^host/(.*)$')


def get_or_create_user_principal(session, principal, createuser=True,
                                 createrealm=True, commitoncreate=False,
                                 comments=None, query_options=None):
    if principal is None:
        return None

    m = principal_re.match(principal)
    if not m:
        raise ArgumentError("User principal '%s' is not valid." % principal)
    realm = m.group(2)
    user = m.group(1)

    m = host_re.match(user)
    if m:
        user = 'aquilonhost'
        # Verify that the host exists in AQDB
        from aquilon.worker.dbwrappers.host import hostname_to_host
        hostname_to_host(session, m.group(1))

    # Short circuit the common case, and optimize it to eager load in
    # a single query since this happens on every command:
    q = session.query(UserPrincipal)
    q = q.filter_by(name=user)
    q = q.join(Realm)
    q = q.filter_by(name=realm)
    q = q.reset_joinpoint()
    q = q.options(contains_eager('realm'),
                  joinedload('role'))
    if query_options:
        q = q.options(*query_options)
    dbuser = q.first()
    if dbuser:
        return dbuser
    # If here, need more complicated behavior...
    dbnobody = Role.get_unique(session, 'nobody', compel=True)
    try:
        dbrealm = Realm.get_unique(session, realm, compel=True)
    except NotFoundException:
        if not createrealm:
            raise ArgumentError("Could not find realm %s to create principal "
                                "%s, use --createrealm to create a new record "
                                "for the realm." % (realm, principal))
        LOGGER.info("Realm %s did not exist, creating...", realm)
        dbrealm = Realm(name=realm)
        session.add(dbrealm)
        LOGGER.info("Creating user %s@%s...", user, realm)
        dbuser = UserPrincipal(name=user, realm=dbrealm, role=dbnobody,
                               comments=comments)
        session.add(dbuser)
        if commitoncreate:
            session.commit()
        return dbuser
    q = session.query(UserPrincipal).filter_by(name=user, realm=dbrealm)
    dbuser = q.first()
    if not dbuser:
        if not createuser:
            raise ArgumentError("Could not find principal %s to permission, "
                                "use --createuser to create a new record for "
                                "the principal." % principal)
        LOGGER.info("User %s did not exist in realm %s, creating...",
                    user, realm)
        dbuser = UserPrincipal(name=user, realm=dbrealm, role=dbnobody,
                               comments=comments)
        session.add(dbuser)
        if commitoncreate:
            session.commit()
    return dbuser


def get_user_principal(session, user):
    """Ignore the realm.  This should probably be re-thought."""
    dbusers = session.query(UserPrincipal).filter_by(name=user).all()
    if len(dbusers) > 1:
        raise InternalError("More than one user found for name %s" % user)
    if len(dbusers) == 0:
        raise NotFoundException("User '%s' not found." % user)
    return dbusers[0]
