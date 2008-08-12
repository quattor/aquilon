#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrapper to make getting an archetype simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.aqdb.cfg.archetype import Archetype


def get_archetype(session, archetype):
    try:
        dbarchetype = session.query(Archetype).filter_by(
                name=archetype).one()
    except InvalidRequestError, e:
        raise NotFoundException("Archetype %s not found: %s"
                % (archetype, e))
    return dbarchetype


#if __name__=='__main__':
