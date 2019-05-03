#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012-2019  Contributor
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

from aquilon.aqdb.model import Building
from aquilon.aqdb.model import City
from aquilon.aqdb.model import Cluster
from aquilon.aqdb.model import DnsDomain
from aquilon.aqdb.model import HardwareEntity
from aquilon.aqdb.model import Machine
from aquilon.aqdb.model import Network
from aquilon.aqdb.model import NetworkDevice
from aquilon.aqdb.model import ServiceMap
from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.location import update_location
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.dbwrappers.change_management import ChangeManagement

class CommandUpdateBuilding(BrokerCommand):
    requires_plenaries = True

    required_parameters = ["building"]

    def render(self, session, logger, plenaries, building, city, address,
               fullname, uri, default_dns_domain, comments,
               netdev_require_rack, user, justification, reason, force_uri,
               next_rackid, force_dns_domain, **kwargs):
        """Extend the superclass method to render the update_building command.

        :param session: an sqlalchemy.orm.session.Session object
        :param logger: an aquilon.worker.logger.RequestLogger object
        :param plenaries: PlenaryCollection()
        :param building: a string with the name of the building
        :param city: a string with the name of the city in which the
                     building is located
        :param address: a string with the address of the building
        :param fullname: a full descriptive name of the building
        :param uri: a reference to a unique identifier in another system
        :param default_dns_domain: a string with the default DNS domain for
                                   the building
        :param comments: a string with comments
        :param netdev_require_rack: if True, restrict this building to require
                                    racks as location for network devices
                                    rather than building
        :param user: a string with the principal / user who invoked the command
        :param justification: authorization tokens (e.g. TCM number or
                              "emergency") to validate the request (None or
                              str)
        :param reason: a human-readable description of why the operation was
                       performed (None or str)
        :param force_uri: if True, bypass URI validation
        :param next_rackid: a numeric part of the next rack name in the
                            building
        :param force_dns_domain: if True, do not run self._validate_dns_domain

        :return: None (on success)

        :raise ArgumentError: on failure (please see the code below to see all
                              the cases when the error is raised)
        """
        dbbuilding = Building.get_unique(session, building, compel=True)

        # Check if the given default DNS domain should be allowed for the
        # given building.
        if default_dns_domain and not force_dns_domain:
            self._validate_dns_domain(default_dns_domain, dbbuilding, session)

        old_city = dbbuilding.city

        dsdb_runner = DSDBRunner(logger=logger)

        if address is not None:
            old_address = dbbuilding.address
            dbbuilding.address = address
            dsdb_runner.update_building(dbbuilding.name, dbbuilding.address,
                                        old_address)

        update_location(dbbuilding, fullname=fullname, comments=comments,
                        netdev_require_rack=netdev_require_rack,
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

    @staticmethod
    def _validate_dns_domain(dns_domain, building, session):
        # Check if the given default DNS domain should be allowed for the
        # given building.
        # If the domain is already assigned to other buildings as their default
        # DNS domain, raise an exception.
        dns_domain = DnsDomain.get_unique(session, dns_domain, compel=True)
        buildings = dns_domain.get_associated_locations(Building, session)
        if building is not None and buildings and building not in buildings:
            raise ArgumentError(
                'DNS domain "{domain}" is already being used as the default '
                'domain for other buildings (e.g. {buildings}).  Please use '
                '--force_dns_domain if you really know what you are doing and '
                'insist on using this domain as the default DNS domain for '
                'building "{building}".'.format(
                    domain=dns_domain.name,
                    # We do not want hundreds of buildings listed in the error
                    # message.
                    buildings=', '.join([b.name for b in buildings[:3]]),
                    building=building.name))
