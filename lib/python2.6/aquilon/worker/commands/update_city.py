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
"""Contains the logic for `aq update city`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Machine, DnsDomain
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.templates.base import Plenary, PlenaryCollection


class CommandUpdateCity(BrokerCommand):

    required_parameters = ["city"]

    def render(self, session, logger, city, timezone, campus,
               default_dns_domain, comments, **arguments):
        dbcity = get_location(session, city=city)

        # Updating machine templates is expensive, so only do that if needed
        update_machines = False

        if timezone is not None:
            dbcity.timezone = timezone
        if comments is not None:
            dbcity.comments = comments
        if default_dns_domain is not None:
            if default_dns_domain:
                dbdns_domain = DnsDomain.get_unique(session, default_dns_domain,
                                                    compel=True)
                dbcity.default_dns_domain = dbdns_domain
            else:
                dbcity.default_dns_domain = None

        prev_campus = None
        dsdb_runner = None
        dsdb_runner = DSDBRunner(logger=logger)
        if campus is not None:
            dbcampus = get_location(session, campus=campus)
            # This one would change the template's locations hence forbidden
            if dbcampus.hub != dbcity.hub:
                # Doing this both to reduce user error and to limit
                # testing required.
                raise ArgumentError("Cannot change campus.  {0} is in {1:l}, "
                                    "while {2:l} is in {3:l}.".format(
                                        dbcampus, dbcampus.hub,
                                        dbcity, dbcity.hub))

            if dbcity.campus:
                prev_campus = dbcity.campus
            dbcity.update_parent(parent=dbcampus)
            update_machines = True

        session.flush()

        if campus is not None:
            if prev_campus:
                prev_name = prev_campus.name
            else:
                prev_name = None
            dsdb_runner.update_city(city, dbcampus.name, prev_name)

        plenaries = PlenaryCollection(logger=logger)
        plenaries.append(Plenary.get_plenary(dbcity))

        if update_machines:
            q = session.query(Machine)
            q = q.filter(Machine.location_id.in_(dbcity.offspring_ids()))
            logger.client_info("Updating %d machines..." % q.count())
            for dbmachine in q:
                plenaries.append(Plenary.get_plenary(dbmachine))

        count = plenaries.write()
        dsdb_runner.commit_or_rollback()
        logger.client_info("Flushed %d templates." % count)
