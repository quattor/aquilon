# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrapper to make getting a status simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.model import Status


def get_status(session, status):
    try:
        dbstatus = session.query(Status).filter_by(name=status).one()
    except InvalidRequestError, e:
        raise NotFoundException("Status %s not found (try one of %s): %s" %
                (status, session.query(Status).all(), e))
    return dbstatus


