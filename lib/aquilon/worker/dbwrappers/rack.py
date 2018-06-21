# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013,2014,2018  Contributor
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

import re

from sqlalchemy.orm.exc import NoResultFound

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Rack
from aquilon.worker.dbwrappers.location import get_location


RACK_ID_REGEX = re.compile(r'^[1-9][0-9]*$')


def get_or_create_rack(session, rackrow, rackcolumn, building=None,
                       room=None, bunker=None, fullname=None, comments=None,
                       uri=None, force_rackid=None, preclude=False):
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

    if force_rackid is not None:
        rackid_numeric = force_rackid.replace(dbbuilding.name, '')
        if not RACK_ID_REGEX.search(rackid_numeric):
            raise ArgumentError("Invalid rack name {}. Correct name format: "
                                "building name + numeric rack ID (integer without leading 0).".format(force_rackid))
        # Allow to fill in rack name gaps without resetting the next_rackid
        if dbbuilding.next_rackid <= int(rackid_numeric):
            dbbuilding.next_rackid = int(rackid_numeric) + 1
    else:
        rackid_numeric = dbbuilding.next_rackid
        dbbuilding.next_rackid += 1

    rack_name = dbbuilding.name + str(rackid_numeric)
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

    dbrack = Rack(name=rack_name, fullname=fullname, parent=dblocation, uri=uri,
                  rack_row=rackrow, rack_column=rackcolumn, comments=comments)
    session.add(dbrack, dbbuilding)
    return dbrack
