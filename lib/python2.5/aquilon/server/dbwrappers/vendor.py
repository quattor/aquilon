# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Wrapper to make getting a vendor simpler."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.hw.vendor import Vendor


def get_vendor(session, vendor):
    try:
        dbvendor = session.query(Vendor).filter_by(name=vendor).one()
    except InvalidRequestError, e:
        raise NotFoundException("Vendor %s not found: %s" % (vendor, e))
    return dbvendor


