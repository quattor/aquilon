# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrapper to make getting a role simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.auth.role import Role


def get_role(session, role):
    try:
        dbrole = session.query(Role).filter_by(name=role).one()
    except InvalidRequestError, e:
        raise NotFoundException("Role %s not found: %s" % (role, e))
    return dbrole


