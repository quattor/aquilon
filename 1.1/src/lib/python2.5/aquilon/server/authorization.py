#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
'''If you can read this, you should be Documenting'''

from aquilon.server.exceptions_ import AuthorizationException
from twisted.python import log

# FIXME: How does this get instantiated?  Should it be a singleton?
class AuthorizationBroker(object):
    """Handles any behind the scenes work in figuring out entitlements."""

    # FIXME: Hard coded check for now.
    def check(self, az_domain, principle, action, resource):
        if principle is None:
            if action == 'show':
                return True
            else:
                log.err("Unauthorized access attempt to %s on %s" % 
                        (action, resource))
                raise AuthorizationException()
        return True

