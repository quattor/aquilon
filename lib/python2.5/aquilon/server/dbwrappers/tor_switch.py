# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrapper to make getting a machine simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.sy.tor_switch import TorSwitch
from aquilon.server.dbwrappers.system import get_system


def get_tor_switch(session, tor_switch):
    dbsystem = get_system(session, tor_switch)
    if not isinstance(dbsystem, TorSwitch):
        raise ArgumentError("'%s' is not a tor_switch." % tor_switch)
    return dbsystem


