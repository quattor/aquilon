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
"""Contains the logic for `aq add hub`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import Location, Company


class CommandAddOrganization(BrokerCommand):

    required_parameters = ["organization"]

    def render(self, session, organization, fullname, comments, **arguments):
        if organization:
            org = session.query(Location).filter_by(location_type='company',
                                                    name=organization).first()
            if org:
                raise ArgumentError("Organization %s already exists." %
                                    organization)
        if not fullname:
            fullname = organization

        dborg = Company(name=organization, fullname=fullname, comments=comments)
        session.add(dborg)
        session.flush()
