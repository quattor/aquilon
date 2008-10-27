#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Authorization stub for simple authorization checks."""

from twisted.python import log

from aquilon.exceptions_ import AuthorizationException
from aquilon.server.dbwrappers.user_principal import (
        get_or_create_user_principal, host_re)


class AuthorizationBroker(object):
    """Handles any behind the scenes work in figuring out entitlements."""

    # Borg
    __shared_state = {}

    def __init__(self):
        self.__dict__ = self.__shared_state

    # FIXME: Hard coded check for now.
    def _check(self, session, dbuser, action, resource, principal):
        if action.startswith('show') or action.startswith('search') \
           or action == 'status':
            return True
        if dbuser is None:
            raise AuthorizationException(
                    "Unauthorized anonymous access attempt to %s on %s" % 
                    (action, resource))
        # Special-casing the aquilon hosts... this is a special user
        # that provides a bucket for all host-generated activity.
        if self._check_aquilonhost(session, dbuser, action, resource,
                                   principal):
            return True
        if dbuser.role.name == 'nobody':
            raise AuthorizationException(
                    "Unauthorized access attempt to %s on %s.  Request permission from 'aqd-eng@morganstanley.com'." % 
                    (action, resource))
        # Right now, anybody in a group can do anything they want, except...
        if action == 'permission' or action == 'flush' or \
           action == 'update_domain':
            if dbuser.role.name != 'aqd_admin':
                raise AuthorizationException(
                        "Must have the aqd_admin role to %s." % action)
        return True

    def _check_aquilonhost(self, session, dbuser, action, resource, principal):
        """ Return true if the incoming user is an aquilon host and this is
            one of the few things that a host is allowed to change on its
            own."""
        if dbuser.name != 'aquilonhost':
            return False
        m = host_re.match(principal)
        if not m:
            return False
        if resource.startswith("/host/%s/" % m.group(1)):
            return True
        return False

    def check(self, session, principal, action, resource):
        dbuser = get_or_create_user_principal(session, principal,
                                              commitoncreate=True)
        return self._check(session, dbuser, action, resource, principal)

