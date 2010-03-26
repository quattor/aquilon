# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Utility/creation wrapper to avoid duplicating code."""


from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Rack
from aquilon.server.broker import force_int
from aquilon.server.dbwrappers.location import get_location


def get_or_create_rack(session, rackid, rackrow, rackcolumn,
                       building=None, room=None, fullname=None, comments=None):
    dblocation = get_location(session, building=building, room=room)
    if not dblocation or not dblocation.building:
        raise ArgumentError("No parent (building or room) given for rack.")
    dbbuilding = dblocation.building

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
            raise ArgumentError("Found rack with name %s but the current column %s does not match given column %s." %
                    (dbrack.name, dbrack.rack_column, rackcolumn))
        return dbrack

    if fullname is None:
        fullname = rack
    dbrack = Rack(name=rack, fullname=fullname, parent=dblocation,
                  rack_row=rackrow, rack_column=rackcolumn, comments=comments)
    session.add(dbrack)
    return dbrack
