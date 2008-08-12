#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrappers for the user_principal table."""

import re

from twisted.python import log

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.auth.user_principal import UserPrincipal
from aquilon.aqdb.auth.realm import Realm
from aquilon.aqdb.auth.role import Role


principal_re = re.compile(r'^(.*)@([^@]+)$')

def get_or_create_user_principal(session, user,
        createuser=True, createrealm=True):
    if user is None:
        return user
    principal = user
    m = principal_re.match(user)
    if not m:
        raise ArgumentError("Could not parse user principal '%s'" % user)
    realm = m.group(2)
    user = m.group(1)
    dbrealm = session.query(Realm).filter_by(name=realm).first()
    dbnobody = session.query(Role).filter_by(name='nobody').first()
    if not dbrealm:
        if not createrealm:
            raise ArgumentError("Could not find realm '%s' to create principal '%s', use --createrealm to create a new record for the realm."
                    % (realm, principal))
        log.msg("Realm %s did not exist, creating..." % realm)
        dbrealm = Realm(name=realm)
        session.save(dbrealm)
        log.msg("Creating user %s..." % principal)
        dbuser = UserPrincipal(name=user, realm=dbrealm, role=dbnobody)
        session.save(dbuser)
        return dbuser
    dbuser = session.query(UserPrincipal).filter_by(
            name=user.strip().lower(), realm=dbrealm).first()
    if not dbuser:
        if not createuser:
            raise ArgumentError("Could not find principal '%s' to permission, use --createuser to create a new record for the principal."
                    % principal)
        log.msg("User %s did not exist in realm %s, creating..." % (user, realm))
        dbuser = UserPrincipal(name=user, realm=dbrealm, role=dbnobody)
        session.save(dbuser)
    return dbuser

#if __name__=='__main__':
