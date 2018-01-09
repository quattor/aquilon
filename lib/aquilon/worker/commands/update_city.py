# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016,2017  Contributor
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
"""Contains the logic for `aq update city`."""

from sqlalchemy.orm import with_polymorphic

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import (City, Campus, HardwareEntity, Machine,
                                NetworkDevice, Cluster, Network)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.dbwrappers.location import update_location
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandUpdateCity(BrokerCommand):
    requires_plenaries = True

    required_parameters = ["city"]

    def render(self, session, logger, plenaries, city, timezone, fullname, campus,
               default_dns_domain, comments, user, justification, reason, **arguments):
        dbcity = City.get_unique(session, city, compel=True)

        plenaries.add(dbcity)

        if timezone is not None:
            dbcity.timezone = timezone

        update_location(dbcity, default_dns_domain=default_dns_domain,
                        fullname=fullname, comments=comments)

        prev_campus = None
        dsdb_runner = None
        dsdb_runner = DSDBRunner(logger=logger)
        if campus is not None:
            dbcampus = Campus.get_unique(session, campus, compel=True)

            HWS = with_polymorphic(HardwareEntity, [Machine, NetworkDevice])
            q = session.query(HWS)
            # HW types which have plenary templates
            q = q.filter(HWS.hardware_type.in_(['machine', 'network_device']))
            q = q.filter(HWS.location_id.in_(dbcity.offspring_ids()))

            # This one would change the template's locations hence forbidden
            # FIXME: allow the change if there are no machines affected
            if dbcampus.hub != dbcity.hub:
                # Doing this both to reduce user error and to limit
                # testing required.
                raise ArgumentError("Cannot change campus.  {0} is in {1:l}, "
                                    "while {2:l} is in {3:l}.".format(
                                        dbcampus, dbcampus.hub,
                                        dbcity, dbcity.hub))

            # Validate ChangeManagement
            cm = ChangeManagement(session, user, justification, reason, logger, self.command, **arguments)
            cm.consider(q)
            plenaries.add(q)

            q = session.query(Cluster)
            q = q.filter(Cluster.location_constraint_id.in_(dbcity.offspring_ids()))
            # Validate ChangeManagement
            # TO DO Either modify validate_prod_cluster method to accept queryset
            # or convert to a list in validate method
            cm.consider(q.all())
            plenaries.add(q)

            q = session.query(Network)
            q = q.filter(Network.location_id.in_(dbcity.offspring_ids()))
            # Validate ChangeManagement
            cm.consider(q)
            plenaries.add(q)

            cm.validate()

            if dbcity.campus:
                prev_campus = dbcity.campus
            dbcity.update_parent(parent=dbcampus)

        session.flush()

        if campus is not None:
            if prev_campus:
                prev_name = prev_campus.name
            else:
                prev_name = None
            dsdb_runner.update_city(city, dbcampus.name, prev_name)

        with plenaries.transaction(verbose=True):
            dsdb_runner.commit_or_rollback()

        return
