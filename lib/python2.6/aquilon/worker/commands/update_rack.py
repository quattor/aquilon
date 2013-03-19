# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
from aquilon.aqdb.model import Machine, DnsDomain
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.templates.base import Plenary, PlenaryCollection


class CommandUpdateRack(BrokerCommand):

    required_parameters = ["rack"]

    def render(self, session, logger, rack, row, column, room, clearroom,
               fullname, default_dns_domain, comments, **arguments):
        dbrack = get_location(session, rack=rack)
        if row is not None:
            dbrack.rack_row = row
        if column is not None:
            dbrack.rack_column = column
        if fullname is not None:
            dbrack.fullname = fullname
        if comments is not None:
            dbrack.comments = comments
        if default_dns_domain is not None:
            if default_dns_domain:
                dbdns_domain = DnsDomain.get_unique(session, default_dns_domain,
                                                    compel=True)
                dbrack.default_dns_domain = dbdns_domain
            else:
                dbrack.default_dns_domain = None
        if room:
            dbroom = get_location(session, room=room)
            # This one would change the template's locations hence forbidden
            if dbroom.building != dbrack.building:
                # Doing this both to reduce user error and to limit
                # testing required.
                raise ArgumentError("Cannot change buildings.  {0} is in {1} "
                                    "while {2} is in {3}.".format(
                                        dbroom, dbroom.building,
                                        dbrack, dbrack.building))
            dbrack.update_parent(parent=dbroom)
        if clearroom:
            if not dbrack.room:
                raise ArgumentError("{0} does not have room information "
                                    "to clear.".format(dbrack))
            dbrack.update_parent(parent=dbrack.room.parent)

        session.flush()

        plenaries = PlenaryCollection(logger=logger)
        q = session.query(Machine)
        q = q.filter(Machine.location_id.in_(dbrack.offspring_ids()))
        for dbmachine in q:
            plenaries.append(Plenary.get_plenary(dbmachine))
        plenaries.write()
