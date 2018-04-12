# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013,2014  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utility/creation wrapper to avoid duplicating code."""

from sqlalchemy.orm.exc import NoResultFound

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Rack
from aquilon.worker.dbwrappers.location import get_location


def get_or_create_rack(session, rackid, rackrow, rackcolumn, building=None,
                       room=None, bunker=None, fullname=None, comments=None,
                       preclude=False):
    dblocation = get_location(session, building=building, room=room,
                              bunker=bunker, compel=True)
    dbbuilding = dblocation.building
    if not dbbuilding:  # pragma: no cover
        raise ArgumentError("The rack must be inside a building.")

    # The database contains normalized values so we have to normalize the input
    # before doing any comparisons.
    if rackrow is not None:
        rackrow = str(rackrow).strip().lower()
    if rackcolumn is not None:
        rackcolumn = str(rackcolumn).strip().lower()
    if rackid is not None:
        rackid = str(rackid).strip().lower()

    rackid_numeric = rackid
    if rackid.startswith(dbbuilding.name):
        rackid_numeric = rackid.replace(dbbuilding.name, '')
    if not rackid_numeric.isdigit():
        raise ArgumentError("Invalid Rack name {}. Correct name format: Building name + numeric Rack ID.".format(rackid))
    rack_name = dbbuilding.name + rackid_numeric

    try:
        dbrack = session.query(Rack).filter_by(name=rack_name).one()
        if rackrow is not None and rackrow != dbrack.rack_row:
            raise ArgumentError("Found rack with name %s, but the current "
                                "row %s does not match given row %s." %
                                (dbrack.name, dbrack.rack_row, rackrow))
        if rackcolumn is not None and rackcolumn != dbrack.rack_column:
            raise ArgumentError("Found rack with name %s, but the current "
                                "column %s does not match given column %s." %
                                (dbrack.name, dbrack.rack_column, rackcolumn))
        if preclude:
            raise ArgumentError("{0} already exists.".format(dbrack))
        return dbrack
    except NoResultFound:
        pass

    if fullname is None:
        fullname = rack_name

    dbrack = Rack(name=rack_name, fullname=fullname, parent=dblocation,
                  rack_row=rackrow, rack_column=rackcolumn, comments=comments)
    session.add(dbrack)
    return dbrack
