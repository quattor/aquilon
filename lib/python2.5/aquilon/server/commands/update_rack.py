# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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
"""Contains the logic for `aq update rack`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Machine
from aquilon.server.broker import BrokerCommand, force_int
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.templates.machine import PlenaryMachineInfo
from aquilon.server.templates.base import PlenaryCollection


class CommandUpdateRack(BrokerCommand):

    required_parameters = ["name"]

    def render(self, session, name, row, column, fullname, comments,
               **arguments):
        dbrack = get_location(session, rack=name)
        if row is not None:
            row = row.strip().lower()
            if not row.isalpha():
                raise ArgumentError("The rack row contained non-alphabet "
                                    "characters.")
            dbrack.rack_row = row
        if column is not None:
            dbrack.rack_column = force_int("column", column)
        if fullname is not None:
            dbrack.fullname = fullname
        if comments is not None:
            dbrack.comments = comments

        session.flush()

        # This cheats, assuming:
        # - only the plenary for machines includes rack information
        # - all machines we care about will have a location of rack
        # The first one should remain valid for awhile.  The second
        # should be fixed once we can easily do searches for any
        # location attribute (as opposed to just the direct link).
        plenaries = PlenaryCollection()
        machines = session.query(Machine).filter_by(location=dbrack).all()
        for dbmachine in machines:
            plenaries.append(PlenaryMachineInfo(dbmachine))
        plenaries.write()

        # XXX: Reconfigure/compile here?

        return


