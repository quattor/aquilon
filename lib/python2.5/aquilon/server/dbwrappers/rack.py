# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Utility/creation wrapper to avoid duplicating code."""


from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.loc.rack import Rack
from aquilon.server.broker import force_int
from aquilon.server.dbwrappers.location import get_location


def get_or_create_rack(session, rackid, building, rackrow, rackcolumn,
        fullname=None, comments=None):
    dbbuilding = get_location(session, building=building)
    if rackcolumn is not None:
        rackcolumn = force_int("rackcolumn", rackcolumn)
    if rackrow is not None:
        rackrow = rackrow.strip().lower()
        if not rackrow.isalpha():
            raise ArgumentError("The rack row contained non-alphabet characters.")
    # Because of http, rackid comes in as a string.  It just
    # gets treated as such here.
    # Check for redundancy...
    if len(rackid) > len(dbbuilding.name) and rackid.startswith(
            dbbuilding.name):
        rack = rackid
    else:
        rack = dbbuilding.name + rackid
    dbrack = session.query(Rack).filter_by(name=rack).first()
    if dbrack:
        if rackrow is not None and rackrow != dbrack.rack_row:
            raise ArgumentError("Found rack with name %s but the current row %s does not match given row %s." %
                    (dbrack.name, dbrack.rack_row, rackrow))
        if rackcolumn is not None and rackcolumn != dbrack.rack_column:
            raise ArgumentError("Found rack with name %s but the current column %d does not match given column %d." %
                    (dbrack.name, dbrack.rack_column, rackcolumn))
        return dbrack

    if fullname is None:
        fullname = rack
    dbrack = Rack(name=rack, fullname=fullname, parent=dbbuilding,
            rack_row=rackrow, rack_column=rackcolumn, comments=comments)
    session.add(dbrack)
    return dbrack


