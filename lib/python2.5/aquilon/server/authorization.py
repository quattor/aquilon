# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Authorization stub for simple authorization checks."""


from twisted.python import log

from aquilon.exceptions_ import AuthorizationException
from aquilon.config import Config
from aquilon.server.dbwrappers.user_principal import host_re


class AuthorizationBroker(object):
    """Handles any behind the scenes work in figuring out entitlements."""

    # Borg
    __shared_state = {}

    def __init__(self):
        self.__dict__ = self.__shared_state
        self.config = Config()

    # FIXME: Hard coded check for now.
    def check(self, principal, dbuser, action, resource):
        if action.startswith('show') or action.startswith('search') \
           or action.startswith('get') or action == 'status':
            return True
        if dbuser is None:
            raise AuthorizationException(
                    "Unauthorized anonymous access attempt to %s on %s" % 
                    (action, resource))
        # Special-casing the aquilon hosts... this is a special user
        # that provides a bucket for all host-generated activity.
        if self._check_aquilonhost(principal, dbuser, action, resource):
            return True
        if dbuser.role.name == 'nobody':
            raise AuthorizationException(
                "Unauthorized access attempt to %s on %s.  "
                "Request permission from '%s'." %
                (action, resource,
                 self.config.get("broker", "authorization_mailgroup")))
        # Right now, anybody in a group can do anything they want, except...
        if action in ['add_archetype', 'update_archetype', 'del_archetype',
                      'add_vendor', 'del_vendor',
                      'add_os', 'del_os']:
            if dbuser.role.name not in ['engineering', 'aqd_admin']:
                raise AuthorizationException(
                    "Must have the engineering or aqd_admin role to %s." %
                    action)
        if action in ['permission', 'flush', 'update_domain', 'add_network']:
            if dbuser.role.name not in ['aqd_admin']:
                raise AuthorizationException(
                    "Must have the aqd_admin role to %s." % action)
        return True

    def _check_aquilonhost(self, principal, dbuser, action, resource):
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


