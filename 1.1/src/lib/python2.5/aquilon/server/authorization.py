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

from aquilon.exceptions_ import AuthorizationException
from twisted.python import log

# FIXME: How does this get instantiated?  Should it be a singleton?
class AuthorizationBroker(object):
    """Handles any behind the scenes work in figuring out entitlements."""
    def __init__(self, dbbroker):
        self.dbbroker = dbbroker

    # FIXME: Hard coded check for now.
    def _check(self, dbuser, az_domain, action, resource):
        if action == 'show':
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
        if action == 'permission':
            if dbuser.role.name != 'aqd_admin':
                raise AuthorizationException(
                        "Must have the aqd_admin role to change permissions.")
        return True

    def check(self, az_domain, principal, action, resource):
        d = self.dbbroker.get_user(True, principal, session=True)
        d = d.addCallback(self._check, az_domain, action, resource)
        return d

