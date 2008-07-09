#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrapper to make getting a service simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.service import Service


def get_service(session, service):
    try:
        dbservice = session.query(Service).filter_by(name=service).one()
    except InvalidRequestError, e:
        raise NotFoundException("Service %s not found: %s" % (service, e))
    return dbservice


#if __name__=='__main__':
