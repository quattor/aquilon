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

import re

from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import Feature
from aquilon.exceptions_ import ArgumentError, UnimplementedError

# Do not allow path components to start with '.' to avoid games like "../foo" or
# hidden directories like ".foo/bar"
_name_re = re.compile(r'^\.|[/\\]\.')


class CommandAddFeature(BrokerCommand):

    required_parameters = ['feature', 'type']

    def render(self, session, feature, type, post_personality, comments,
               **arguments):
        Feature.validate_type(type)

        if _name_re.search(feature):
            raise ArgumentError("Path components in the feature name must not "
                                "start with a dot.")

        cls = Feature.__mapper__.polymorphic_map[type].class_

        if post_personality and not cls.post_personality_allowed:
            raise UnimplementedError("The post_personality attribute is "
                                     "implemented only for host features.")

        cls.get_unique(session, name=feature, preclude=True)

        dbfeature = cls(name=feature, post_personality=post_personality,
                        comments=comments)
        session.add(dbfeature)

        session.flush()

        return
