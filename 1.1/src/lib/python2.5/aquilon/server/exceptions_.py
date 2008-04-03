#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Exceptions to be used by the Aquilon Server"""

from aquilon.exceptions_ import AquilonError

class AuthorizationException(AquilonError):
    '''Raised when a principle is not authorized to perform a given
    action on a resource.

    '''

