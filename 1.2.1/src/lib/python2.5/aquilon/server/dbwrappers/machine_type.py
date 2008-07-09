#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrapper to make getting a machine_type simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.hardware import MachineType


def get_machine_type(session, machine_type):
    try:
        dbmachine_type = session.query(MachineType).filter_by(type=machine_type).one()
    except InvalidRequestError, e:
        raise NotFoundException("MachineType %s not found: %s" % (machine_type, e))
    return dbmachine_type


#if __name__=='__main__':
