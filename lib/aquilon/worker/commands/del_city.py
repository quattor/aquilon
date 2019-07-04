# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008-2013,2015-2016,2019  Contributor
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
"""Contains the logic for `aq del city`."""

from aquilon.aqdb.model import City
from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.commands.del_location import CommandDelLocation


class CommandDelCity(CommandDelLocation):
    requires_plenaries = True

    required_parameters = ["city"]

    # noinspection PyMethodOverriding
    def render(self, session, logger, plenaries, city, force_if_orphaned,
               **arguments):
        """Extend the superclass method to render the del_city command.

        :param session: an sqlalchemy.orm.session.Session object
        :param logger: an aquilon.worker.logger.RequestLogger object
        :param plenaries: PlenaryCollection()
        :param city: a string with the name of the city
        :param force_if_orphaned: if True, do not run self._validate_dns_domain

        :return: None (on success)

        :raise ArgumentError: on failure (please see the code below to see all
                              the cases when the error is explicitly raised)
        """
        dbcity = City.get_unique(session, city, compel=True)
        country = None
        if dbcity.country is None and not force_if_orphaned:
            raise ArgumentError(
                'City "{}" is not associated with any country.  Please use '
                '--force_if_orphaned if you want to delete it -- be advised '
                'that such an operation cannot be automatically rolled back in'
                ' DSDB.'.format(dbcity.name))
        elif dbcity.country is not None:
            country = dbcity.country.name
        fullname = dbcity.fullname
        plenaries.add(dbcity)
        CommandDelLocation.render(self, session=session, name=city,
                                  type='city', **arguments)
        session.flush()
        with plenaries.transaction():
            dsdb_runner = DSDBRunner(logger=logger)
            dsdb_runner.del_city(dbcity.name, country, fullname)
            dsdb_runner.commit_or_rollback()
        return
