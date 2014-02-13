# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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
"""Contains the logic for `aq update share`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Share
from aquilon.worker.broker import BrokerCommand, validate_basic
from aquilon.worker.dbwrappers.resources import get_resource_holder
from aquilon.worker.templates import Plenary, PlenaryCollection


class CommandUpdateShare(BrokerCommand):

    required_parameters = ["share"]

    def render(self, session, logger, share, latency_threshold,
               comments, **arguments):

        validate_basic("share", share)

        q = session.query(Share).filter_by(name=share)

        if q.count() == 0:
            raise ArgumentError("Share %s is not used on any resource and "
                                "cannot be modified" % share)
        plenaries = PlenaryCollection(logger=logger)

        for dbshare in q.all():
            if latency_threshold:
                dbshare.latency_threshold = latency_threshold

            if comments:
                dbshare.comments = comments

                plenaries.append(Plenary.get_plenary(dbshare))

        session.flush()
        plenaries.write()

        return
