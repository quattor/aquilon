# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrapper to make getting a personality simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.server.dbwrappers.archetype import get_archetype
from aquilon.aqdb.cfg import Archetype, Personality

def get_personality(session, archetype, personality):
    try:
        dbarchetype = get_archetype(session, archetype)

        dbpersonality = session.query(Personality).filter_by(
            name=personality,archetype=dbarchetype).one()

    except InvalidRequestError, e:
        raise NotFoundException("Personality %s in Archetype %s not found: %s"
                % (personality, archetype, e))
    return dbpersonality
