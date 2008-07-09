#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Authorization stub for simple authorization checks."""

from twisted.python import log

from aquilon.exceptions_ import AuthorizationException
from aquilon.server.dbwrappers.user_principal import (
        get_or_create_user_principal)


class AuthorizationBroker(object):
    """Handles any behind the scenes work in figuring out entitlements."""

    # Borg
    __shared_state = {}

    def __init__(self):
        self.__dict__ = self.__shared_state

    # FIXME: Hard coded check for now.
    def _check(self, session, dbuser, action, resource):
        if action.startswith('show') or action == 'status':
            return True
        if dbuser is None:
            raise AuthorizationException(
                    "Unauthorized anonymous access attempt to %s on %s" % 
                    (action, resource))
        if dbuser.role.name == 'nobody':
            raise AuthorizationException(
                    "Unauthorized access attempt to %s on %s.  Request permission from 'aqd-eng@morganstanley.com'." % 
                    (action, resource))
        # Right now, anybody in a group can do anything they want, except...
        if action == 'permission' or action == 'regenerate_templates':
            if dbuser.role.name != 'aqd_admin':
                raise AuthorizationException(
                        "Must have the aqd_admin role to %s." % action)
        return True

    def check(self, session, principal, action, resource):
        dbuser = get_or_create_user_principal(session, principal)
        return self._check(session, dbuser, action, resource)

