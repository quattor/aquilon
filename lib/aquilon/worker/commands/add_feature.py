# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014,2015  Contributor
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

import re

from aquilon.exceptions_ import ArgumentError, UnimplementedError
from aquilon.aqdb.model import Feature
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.grn import lookup_grn

# Do not allow path components to start with '.' to avoid games like "../foo" or
# hidden directories like ".foo/bar"
_name_re = re.compile(r'^\.|[/\\]\.')


class CommandAddFeature(BrokerCommand):

    required_parameters = ['feature', 'type']

    def render(self, session, feature, type, post_personality, comments,
               grn, eon_id, visibility, activation, deactivation, logger, **_):
        cls = Feature.polymorphic_subclass(type, "Unknown feature type")

        if _name_re.search(feature):
            raise ArgumentError("Path components in the feature name must not "
                                "start with a dot.")

        if post_personality and not cls.post_personality_allowed:
            raise UnimplementedError("The post_personality attribute is "
                                     "implemented only for host features.")

        if not (grn or eon_id):
            raise ArgumentError("GRN or EON ID is required for adding a "
                                "feature.")

        cls.get_unique(session, name=feature, preclude=True)

        dbgrn = lookup_grn(session, grn, eon_id, logger=logger,
                           config=self.config)

        if not visibility:
            visibility = "restricted"

        dbfeature = cls(name=feature, post_personality=post_personality,
                        owner_grn=dbgrn, visibility=visibility,
                        activation=activation, deactivation=deactivation,
                        comments=comments)
        session.add(dbfeature)

        session.flush()

        return
