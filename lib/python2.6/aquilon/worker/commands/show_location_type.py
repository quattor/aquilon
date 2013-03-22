# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Contains the logic for `aq show location --type`."""


from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import subqueryload

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import Location
from aquilon.worker.formats.location import LocationList


class CommandShowLocationType(BrokerCommand):

    required_parameters = ["type"]

    def render(self, session, type, name, **arguments):
        if type not in Location.__mapper__.polymorphic_map:
            raise ArgumentError("Unknown location type '%s'." % type)

        cls = Location.__mapper__.polymorphic_map[type].class_
        query = session.query(cls)
        query = query.options(subqueryload('parents'),
                              subqueryload('default_dns_domain'))

        if name:
            query = query.filter_by(name=name)
            try:
                return query.one()
            except NoResultFound:
                raise NotFoundException("%s %s not found." %
                                        (cls._get_class_label(), name))

        return LocationList(query.order_by(Location.location_type,
                                           Location.name).all())
