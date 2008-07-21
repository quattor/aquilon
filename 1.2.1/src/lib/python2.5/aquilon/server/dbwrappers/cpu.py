#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrapper to make getting a cpu simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.hw.cpu import Cpu


# FIXME: CPU is not specified uniquely with just name!
def get_cpu(session, cpu):
    try:
        dbcpu = session.query(Cpu).filter_by(name=cpu).one()
    except InvalidRequestError, e:
        raise NotFoundException("Cpu %s not uniquely identified: %s" % (cpu, e))
    return dbcpu


#if __name__=='__main__':
