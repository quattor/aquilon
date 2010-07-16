# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Wrappers for the user_principal table."""


import re
import logging

from sqlalchemy.orm import eagerload

from aquilon.exceptions_ import ArgumentError, InternalError, NotFoundException
from aquilon.aqdb.model import Role, Realm, UserPrincipal
from aquilon.server.dbwrappers.host import hostname_to_host


LOGGER = logging.getLogger('aquilon.server.dbwrappers.user_principal')
principal_re = re.compile(r'^(.*)@([^@]+)$')
host_re = re.compile(r'^host/(.*)@([^@]+)$')

def get_or_create_user_principal(session, user,
        createuser=True, createrealm=True, commitoncreate=False):
    if user is None:
        return user
    principal = user
    m = principal_re.match(user)
    if not m:
        raise ArgumentError("User principal '%s' is not valid." % user)
    realm = m.group(2)
    user = m.group(1)
    m = host_re.match(principal)
    if m:
        user = 'aquilonhost'
        hostname = m.group(1)
        # Don't actually need the host... just need to verify that it's
        # in aqdb.
        dbhost = hostname_to_host(session, hostname)
    # Short circuit the common case, and optimize it to eager load in
    # a single query since this happens on every command:
    q = session.query(UserPrincipal).filter_by(name=user)
    q = q.options(eagerload('role'), eagerload('realm'))
    q = q.join('realm').filter_by(name=realm)
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
        LOGGER.info("Realm %s did not exist, creating..." % realm)
        dbrealm = Realm(name=realm)
        session.add(dbrealm)
        LOGGER.info("Creating user %s@%s..." % (user, realm))
        dbuser = UserPrincipal(name=user, realm=dbrealm, role=dbnobody)
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
        LOGGER.info("User %s did not exist in realm %s, creating..." %
                    (user, realm))
        dbuser = UserPrincipal(name=user, realm=dbrealm, role=dbnobody)
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
