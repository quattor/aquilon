#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrapper to make getting a machine simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.hw.tor_switch import TorSwitch
from aquilon.server.dbwrappers.a_name import get_a_name


def get_tor_switch(session, tor_switch):
    dba_name = get_a_name(session, tor_switch)
    try:
        dbtor_switch = session.query(TorSwitch).filter_by(a_name=dba_name).one()
    except InvalidRequestError, e:
        raise NotFoundException("TorSwitch %s not found: %s" % (tor_switch, e))
    return dbtor_switch


#if __name__=='__main__':
