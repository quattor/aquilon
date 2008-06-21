#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrapper to make getting a machine simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.hardware import Machine


def get_machine(session, machine):
    try:
        dbmachine = session.query(Machine).filter_by(name=machine).one()
    except InvalidRequestError, e:
        raise NotFoundException("Machine %s not found: %s" % (machine, e))
    return dbmachine


#if __name__=='__main__':
