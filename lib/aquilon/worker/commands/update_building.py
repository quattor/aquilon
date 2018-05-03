# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014,2015,2016,2017,2018  Contributor
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
"""Contains the logic for `aq update building`."""

from sqlalchemy.orm import with_polymorphic

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import (Building, City, HardwareEntity, Machine,
                                NetworkDevice, ServiceMap, Cluster, Network)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.location import update_location
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandUpdateBuilding(BrokerCommand):
    requires_plenaries = True

    required_parameters = ["building"]

    def render(self, session, logger, plenaries, building, city, address,
               fullname, uri, default_dns_domain, comments, user,
               justification, reason, force_uri, next_rackid, **kwargs):
        dbbuilding = Building.get_unique(session, building, compel=True)

        old_city = dbbuilding.city

        dsdb_runner = DSDBRunner(logger=logger)

        if address is not None:
            old_address = dbbuilding.address
            dbbuilding.address = address
            dsdb_runner.update_building(dbbuilding.name, dbbuilding.address,
                                        old_address)

        update_location(dbbuilding, fullname=fullname, comments=comments,
                        uri=uri, default_dns_domain=default_dns_domain,
                        force_uri=force_uri, logger=logger, next_rackid=next_rackid)

        if city:
            dbcity = City.get_unique(session, city, compel=True)

            HWS = with_polymorphic(HardwareEntity, [Machine, NetworkDevice])
            q = session.query(HWS)
            # HW types which have plenary templates
            q = q.filter(HWS.hardware_type.in_(['machine', 'network_device']))
            q = q.filter(HWS.location_id.in_(dbbuilding.offspring_ids()))

            # Validate ChangeManagement
            cm = ChangeManagement(session, user, justification, reason, logger, self.command, **kwargs)
            cm.consider(q)
            # This one would change the template's locations hence forbidden
            if dbcity.hub != dbbuilding.hub and q.count():
                # Doing this both to reduce user error and to limit
                # testing required.
                raise ArgumentError("Cannot change hubs. {0} is in {1:l}, "
                                    "while {2:l} is in {3:l}."
                                    .format(dbcity, dbcity.hub, dbbuilding,
                                            dbbuilding.hub))

            # issue svcmap warnings
            maps = session.query(ServiceMap).filter_by(location=old_city).count()

            if maps:
                logger.client_info("There are {0} service(s) mapped to the "
                                   "old location of the ({1:l}), please "
                                   "review and manually update mappings for "
                                   "the new location as needed."
                                   .format(maps, dbbuilding.city))

            plenaries.add(q)

            q = session.query(Cluster)
            q = q.filter(Cluster.location_constraint_id.in_(dbbuilding.offspring_ids()))
            # Validate ChangeManagement
            # TO DO Either modify validate_prod_cluster method to accept queryset
            # or convert to a list in validate method
            cm.consider(q.all())
            plenaries.add(q)

            q = session.query(Network)
            q = q.filter(Network.location_id.in_(dbbuilding.offspring_ids()))
            # Validate ChangeManagement
            cm.consider(q)
            plenaries.add(q)
            cm.validate()
            dbbuilding.update_parent(parent=dbcity)

            if old_city.campus and (old_city.campus != dbcity.campus):
                dsdb_runner.del_campus_building(old_city.campus, building)

            if dbcity.campus and (old_city.campus != dbcity.campus):
                dsdb_runner.add_campus_building(dbcity.campus, building)

        session.flush()

        if plenaries.plenaries:
            with plenaries.transaction():
                dsdb_runner.commit_or_rollback()
        else:
            dsdb_runner.commit_or_rollback()

        return
