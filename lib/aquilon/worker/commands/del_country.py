# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008-2011,2013,2019  Contributor
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
"""Contains the logic for `aq del country`."""

from aquilon.aqdb.model import City
from aquilon.aqdb.model import Location
from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.del_location import CommandDelLocation


class CommandDelCountry(CommandDelLocation):

    required_parameters = ['country']

    def render(self, session, country, force_non_empty, **arguments):
        """Extend the superclass method to render the del_country command.

        :param session: an sqlalchemy.orm.session.Session object
        :param country: a string with the name of the country to be deleted
        :param force_non_empty: if True, do not check if the country still
                                contains any cities

        :return: None (on success)

        :raise ArgumentError: on failure (please see the code below to see all
                              the cases when the error is raised)
        """

        dblocation = Location.get_unique(
            session, name=country, location_type='country', compel=True)

        if not force_non_empty and dblocation.contains_any_location_of_class(
                City, session):
            # noinspection PyStringFormat
            raise ArgumentError(
                'Could not delete {0:l}, at least one city found in this '
                'country.'.format(dblocation))

        return CommandDelLocation.render(
            self, session=session, name=country, type='country', **arguments)
