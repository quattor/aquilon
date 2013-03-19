# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013  Contributor
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
"""Contains the logic for `aq update building`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import (Machine, ServiceMap, PersonalityServiceMap,
                                DnsDomain)
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.templates.machine import PlenaryMachineInfo
from aquilon.worker.templates.base import PlenaryCollection


# based on update_rack
class CommandUpdateBuilding(BrokerCommand):

    required_parameters = ["building"]

    def render(self, session, logger, building, city, address,
               fullname, default_dns_domain, comments, **arguments):
        dbbuilding = get_location(session, building=building)

        old_city = dbbuilding.city

        dsdb_runner = DSDBRunner(logger=logger)

        if address is not None:
            old_address = dbbuilding.address
            dbbuilding.address = address
            dsdb_runner.update_building(dbbuilding.name, dbbuilding.address,
                                        old_address)
        if fullname is not None:
            dbbuilding.fullname = fullname
        if comments is not None:
            dbbuilding.comments = comments
        if default_dns_domain is not None:
            if default_dns_domain:
                dbdns_domain = DnsDomain.get_unique(session, default_dns_domain,
                                                    compel=True)
                dbbuilding.default_dns_domain = dbdns_domain
            else:
                dbbuilding.default_dns_domain = None

        plenaries = PlenaryCollection(logger=logger)
        if city:
            dbcity = get_location(session, city=city)

            # This one would change the template's locations hence forbidden
            if dbcity.hub != dbbuilding.hub:
                # Doing this both to reduce user error and to limit
                # testing required.
                raise ArgumentError("Cannot change hubs. {0} is in {1} "
                                    "while {2} is in {3}.".format(
                                        dbcity, dbcity.hub,
                                        dbbuilding, dbbuilding.hub))

            # issue svcmap warnings
            maps = 0
            for map_type in [ServiceMap, PersonalityServiceMap]:
                maps = maps + session.query(map_type).\
                    filter_by(location=old_city).count()

            if maps > 0:
                logger.client_info("There are {0} service(s) mapped to the "
                                   "old location of the ({1:l}), please "
                                   "review and manually update mappings for "
                                   "the new location as needed.".format(
                                       maps, dbbuilding.city))

            dbbuilding.update_parent(parent=dbcity)

            if old_city.campus and (old_city.campus != dbcity.campus):
                dsdb_runner.del_campus_building(old_city.campus, building)

            if dbcity.campus and (old_city.campus != dbcity.campus):
                dsdb_runner.add_campus_building(dbcity.campus, building)

            query = session.query(Machine)
            query = query.filter(Machine.location_id.in_(dbcity.offspring_ids()))

            for dbmachine in query:
                plenaries.append(PlenaryMachineInfo(dbmachine, logger=logger))

        session.flush()

        if plenaries.plenaries:
            with plenaries.get_write_key() as key:
                plenaries.stash()
                try:
                    plenaries.write(locked=True)
                    dsdb_runner.commit_or_rollback()
                except:
                    plenaries.restore_stash()
        else:
            dsdb_runner.commit_or_rollback()

        return
